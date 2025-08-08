# app/services/base_generative_service.py
import hashlib  # <-- NOVA IMPORTAÇÃO para criar chaves de cache estáveis
import logging
import os
import time
from datetime import datetime, timedelta
from flask import request, current_app
from flask_login import current_user

import google.generativeai as genai

from app import cache, db  # <-- NOVA IMPORTAÇÃO
from app.models.gemini_usage import GeminiUsageLog  # <-- NOVA IMPORTAÇÃO


class BaseGenerativeService:
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self._google_api_key = None
        
        # Rate limiting para APIs Gemini
        self._api_usage = {
            "GOOGLE_API_KEY_1": {"last_used": None, "daily_count": 0, "last_reset": None},
            "GOOGLE_API_KEY_2": {"last_used": None, "daily_count": 0, "last_reset": None}
        }
        
        # Limites de rate (ajuste conforme necessário)
        self._rate_limits = {
            "requests_per_day": 45,  # Deixe margem de segurança
            "min_interval_seconds": 2  # Intervalo mínimo entre requisições
        }

        try:
            # Tenta usar GOOGLE_API_KEY_1 primeiro, depois GOOGLE_API_KEY como fallback
            # IMPORTANTE: Configure no .env ou variáveis de ambiente:
            # - GOOGLE_API_KEY_1 (API Key principal para inicialização)
            # - GOOGLE_API_KEY_2 (API Key de backup para fallback)
            self._google_api_key = os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY")
            if not self._google_api_key:
                self.logger.error(
                    "API Key do Google (GOOGLE_API_KEY_1 ou GOOGLE_API_KEY) não encontrada nas variáveis de ambiente."
                )
                raise RuntimeError(
                    "API Key do Google (GOOGLE_API_KEY_1 ou GOOGLE_API_KEY) não configurada nas variáveis de ambiente."
                )

            genai.configure(api_key=self._google_api_key)
            self.logger.info(
                "Configuração da API Key do Google bem-sucedida para o serviço."
            )

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
            ]

            self.model = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings,
                generation_config=generation_config,
            )
            self.logger.info(
                f"Modelo Gemini '{self.model.model_name}' inicializado com sucesso para {self.__class__.__name__}."
            )

        except RuntimeError as rte:
            self.logger.critical(
                f"Falha na inicialização do serviço (configuração da API): {rte}"
            )
            raise
        except Exception as e:
            self.logger.critical(
                f"Falha catastrófica na inicialização do serviço ({self.__class__.__name__}): {e}",
                exc_info=True,
            )
            self.model = None
            raise RuntimeError(
                f"Falha catastrófica na inicialização do serviço de IA: {e}"
            ) from e

    def _log_api_usage(self, api_key_name: str, prompt_length: int, response_length: int = None, 
                      cache_hit: bool = False, success: bool = True, error_message: str = None):
        """Registra o uso da API no banco de dados."""
        try:
            # Obtém informações do usuário atual
            user_id = None
            username = None
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
                username = current_user.username
            
            # Obtém informações da requisição
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent')
            
            # Cria o log
            log_entry = GeminiUsageLog(
                user_id=user_id,
                username=username,
                api_key_name=api_key_name,
                service_name=self.__class__.__name__,
                prompt_length=prompt_length,
                response_length=response_length,
                cache_hit=cache_hit,
                success=success,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Salva no banco
            db.session.add(log_entry)
            db.session.commit()
            
            self.logger.info(f"📊 Log de uso registrado: {api_key_name} - {username or 'Anônimo'} - Cache: {'HIT' if cache_hit else 'MISS'}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao registrar log de uso: {e}")
            # Não falha a operação principal se o log falhar
            db.session.rollback()

    def _check_rate_limit(self, api_key_name: str) -> bool:
        """Verifica se a API key pode ser usada baseado no rate limiting."""
        now = datetime.now()
        usage = self._api_usage[api_key_name]
        
        # Reset diário se necessário
        if usage["last_reset"] is None or (now - usage["last_reset"]).days >= 1:
            usage["daily_count"] = 0
            usage["last_reset"] = now
            self.logger.info(f"🔄 Reset diário do contador para {api_key_name}")
        
        # Verifica limite diário
        if usage["daily_count"] >= self._rate_limits["requests_per_day"]:
            self.logger.warning(f"⚠️ Limite diário atingido para {api_key_name}: {usage['daily_count']}/{self._rate_limits['requests_per_day']}")
            return False
        
        # Verifica intervalo mínimo
        if usage["last_used"] and (now - usage["last_used"]).total_seconds() < self._rate_limits["min_interval_seconds"]:
            self.logger.warning(f"⚠️ Intervalo mínimo não respeitado para {api_key_name}")
            return False
        
        return True

    def _update_usage(self, api_key_name: str):
        """Atualiza o contador de uso da API key."""
        now = datetime.now()
        self._api_usage[api_key_name]["last_used"] = now
        self._api_usage[api_key_name]["daily_count"] += 1
        self.logger.info(f"📊 Uso atualizado para {api_key_name}: {self._api_usage[api_key_name]['daily_count']}/{self._rate_limits['requests_per_day']}")

    def _generate_cache_key(self, prompt_final: str) -> str:
        """Gera uma chave de cache SHA256 para o prompt."""
        cache_key = hashlib.sha256(prompt_final.encode("utf-8")).hexdigest()
        self.logger.info(f"🔑 Chave de cache gerada: {cache_key[:16]}...")
        return cache_key

    # APLICAÇÃO DO CACHE COM O DECORATOR @cache.memoize
    @cache.memoize(timeout=3600)  # Cache por 1 hora
    def _call_generative_model(self, prompt_final: str) -> str:
        import google.generativeai as genai
        import os
        
        # Log detalhado do cache
        cache_key = self._generate_cache_key(prompt_final)
        self.logger.info(f"🚀 CACHE MISS - Nova consulta para chave: {cache_key[:16]}...")
        self.logger.info(f"📝 Prompt (primeiros 100 chars): {prompt_final[:100]}...")
        
        if not isinstance(prompt_final, str) or not prompt_final.strip():
            self.logger.warning("Prompt final está vazio ou não é uma string.")
            raise ValueError("Prompt final para a IA não pode ser vazio.")

        # Configuração das API Keys para fallback automático
        # IMPORTANTE: Configure no .env ou variáveis de ambiente:
        # - GOOGLE_API_KEY_1 (API Key principal)
        # - GOOGLE_API_KEY_2 (API Key de backup/fallback)
        api_keys = [
            ("GOOGLE_API_KEY_1", os.environ.get("GOOGLE_API_KEY_1")),
            ("GOOGLE_API_KEY_2", os.environ.get("GOOGLE_API_KEY_2"))
        ]
        last_exception = None
        
        for api_key_name, api_key in api_keys:
            if not api_key:
                self.logger.warning(f"{api_key_name} não configurada, pulando...")
                continue
                
            # Verifica rate limiting
            if not self._check_rate_limit(api_key_name):
                self.logger.warning(f"⏰ Rate limit atingido para {api_key_name}, tentando próxima...")
                continue
                
            try:
                genai.configure(api_key=api_key)
                self.logger.info(f"🔑 Usando {api_key_name} para chamada Gemini.")
                
                # Recria o modelo para garantir que está usando a API Key correta
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "text/plain",
                }
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                model = genai.GenerativeModel(
                    model_name=getattr(self, 'model', None).model_name if getattr(self, 'model', None) else "gemini-1.5-flash-latest",
                    safety_settings=safety_settings,
                    generation_config=generation_config,
                )
                self.logger.info(f"🤖 Enviando prompt para o modelo Gemini ({api_key_name})")
                response = model.generate_content(prompt_final)
                self.logger.debug(f"Resposta bruta da API Gemini: {response}")

                # Atualiza contador de uso
                self._update_usage(api_key_name)

                if response.parts:
                    texto_processado = "".join(
                        part.text for part in response.parts if hasattr(part, "text")
                    )
                    if texto_processado:
                        self.logger.info(f"✅ Resposta da IA processada com sucesso (via response.parts) - {len(texto_processado)} chars")
                        self.logger.info(f"💾 Salvando no cache com chave: {cache_key[:16]}...")
                        
                        # Registra log de sucesso
                        self._log_api_usage(
                            api_key_name=api_key_name,
                            prompt_length=len(prompt_final),
                            response_length=len(texto_processado),
                            cache_hit=False,
                            success=True
                        )
                        
                        return texto_processado
                    elif (
                        response.prompt_feedback
                        and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED"
                    ):
                        block_reason_detail = (
                            response.prompt_feedback.block_reason_message
                            or str(response.prompt_feedback.block_reason)
                        )
                        self.logger.warning(f"🚫 Conteúdo bloqueado pela IA (detectado em parts). Motivo: {block_reason_detail}")
                        
                        # Registra log de erro
                        self._log_api_usage(
                            api_key_name=api_key_name,
                            prompt_length=len(prompt_final),
                            cache_hit=False,
                            success=False,
                            error_message=f"Conteúdo bloqueado: {block_reason_detail}"
                        )
                        
                        raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
                    else:
                        self.logger.warning("⚠️ Resposta da IA (via parts) não contém texto processado ou partes válidas.")
                        
                        # Registra log de erro
                        self._log_api_usage(
                            api_key_name=api_key_name,
                            prompt_length=len(prompt_final),
                            cache_hit=False,
                            success=False,
                            error_message="Resposta vazia ou inválida"
                        )
                        
                        raise ValueError("Resposta da IA (via parts) está vazia ou inválida.")

                elif hasattr(response, "text") and response.text:
                    self.logger.info(f"✅ Resposta da IA processada com sucesso (via response.text) - {len(response.text)} chars")
                    self.logger.info(f"💾 Salvando no cache com chave: {cache_key[:16]}...")
                    
                    # Registra log de sucesso
                    self._log_api_usage(
                        api_key_name=api_key_name,
                        prompt_length=len(prompt_final),
                        response_length=len(response.text),
                        cache_hit=False,
                        success=True
                    )
                    
                    return response.text

                elif (
                    response.prompt_feedback
                    and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED"
                ):
                    block_reason_detail = (
                        response.prompt_feedback.block_reason_message
                        or str(response.prompt_feedback.block_reason)
                    )
                    self.logger.warning(f"🚫 Conteúdo bloqueado pela IA (sem partes/texto, mas com feedback). Motivo: {block_reason_detail}")
                    
                    # Registra log de erro
                    self._log_api_usage(
                        api_key_name=api_key_name,
                        prompt_length=len(prompt_final),
                        cache_hit=False,
                        success=False,
                        error_message=f"Conteúdo bloqueado: {block_reason_detail}"
                    )
                    
                    raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
                else:
                    self.logger.warning("⚠️ Resposta da API Gemini não contém 'text', 'parts' válidas ou feedback de bloqueio claro.")
                    
                    # Registra log de erro
                    self._log_api_usage(
                        api_key_name=api_key_name,
                        prompt_length=len(prompt_final),
                        cache_hit=False,
                        success=False,
                        error_message="Formato de resposta inesperado"
                    )
                    
                    raise ValueError("Resposta da API Gemini está em formato inesperado ou vazia.")
            except Exception as e:
                self.logger.error(f"❌ Erro ao tentar {api_key_name}: {e}", exc_info=True)
                
                # Registra log de erro
                self._log_api_usage(
                    api_key_name=api_key_name,
                    prompt_length=len(prompt_final),
                    cache_hit=False,
                    success=False,
                    error_message=str(e)
                )
                
                last_exception = e
                continue
        
        # Se chegou aqui, todas as tentativas falharam
        if last_exception:
            raise RuntimeError(f"Todas as APIs Gemini falharam. Último erro: {last_exception}")
        else:
            raise RuntimeError("Nenhuma API Key Gemini configurada. Configure GOOGLE_API_KEY_1 ou GOOGLE_API_KEY_2 no .env")

    def _call_generative_model_with_cache_logging(self, prompt_final: str) -> str:
        """Versão da função com logs detalhados de cache."""
        cache_key = self._generate_cache_key(prompt_final)
        
        # Verifica se existe no cache
        try:
            cached_result = cache.get(cache_key)
            if cached_result:
                self.logger.info(f"🎯 CACHE HIT - Resposta encontrada no cache para chave: {cache_key[:16]}...")
                self.logger.info(f"📊 Tamanho da resposta em cache: {len(cached_result)} chars")
                
                # Registra log de cache hit
                self._log_api_usage(
                    api_key_name="CACHE",
                    prompt_length=len(prompt_final),
                    response_length=len(cached_result),
                    cache_hit=True,
                    success=True
                )
                
                return cached_result
            else:
                self.logger.info(f"🚀 CACHE MISS - Chave não encontrada: {cache_key[:16]}...")
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao verificar cache: {e}")
        
        # Se não está no cache, chama a função original
        result = self._call_generative_model(prompt_final)
        self.logger.info(f"💾 Resposta salva no cache com chave: {cache_key[:16]}...")
        return result
