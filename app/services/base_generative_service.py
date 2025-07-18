# app/services/base_generative_service.py
import hashlib  # <-- NOVA IMPORTAÇÃO para criar chaves de cache estáveis
import logging
import os

import google.generativeai as genai

from app import cache  # <-- NOVA IMPORTAÇÃO


class BaseGenerativeService:
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self._google_api_key = None

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

    def _generate_cache_key(self, prompt_final: str) -> str:
        """Gera uma chave de cache SHA256 para o prompt."""
        return hashlib.sha256(prompt_final.encode("utf-8")).hexdigest()

    # APLICAÇÃO DO CACHE COM O DECORATOR @cache.memoize
    @cache.memoize()
    def _call_generative_model(self, prompt_final: str) -> str:
        import google.generativeai as genai
        import os
        
        if not isinstance(prompt_final, str) or not prompt_final.strip():
            self.logger.warning("Prompt final está vazio ou não é uma string.")
            raise ValueError("Prompt final para a IA não pode ser vazio.")

        # Configuração das API Keys para fallback automático
        # IMPORTANTE: Configure no .env ou variáveis de ambiente:
        # - GOOGLE_API_KEY_1 (API Key principal)
        # - GOOGLE_API_KEY_2 (API Key de backup/fallback)
        api_keys = [
            os.environ.get("GOOGLE_API_KEY_1"),
            os.environ.get("GOOGLE_API_KEY_2")
        ]
        last_exception = None
        for idx, api_key in enumerate(api_keys, 1):
            if not api_key:
                self.logger.warning(f"GOOGLE_API_KEY_{idx} não configurada, pulando...")
                continue
            try:
                genai.configure(api_key=api_key)
                self.logger.info(f"Usando GOOGLE_API_KEY_{idx} para chamada Gemini.")
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
                self.logger.info(f"CACHE MISS. Enviando novo prompt para o modelo Gemini (API {idx}) (primeiros 100 chars): {prompt_final[:100]}...")
                response = model.generate_content(prompt_final)
                self.logger.debug(f"Resposta bruta da API Gemini: {response}")

                if response.parts:
                    texto_processado = "".join(
                        part.text for part in response.parts if hasattr(part, "text")
                    )
                    if texto_processado:
                        self.logger.info("Resposta da IA processada com sucesso (via response.parts).")
                        return texto_processado
                    elif (
                        response.prompt_feedback
                        and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED"
                    ):
                        block_reason_detail = (
                            response.prompt_feedback.block_reason_message
                            or str(response.prompt_feedback.block_reason)
                        )
                        self.logger.warning(f"Conteúdo bloqueado pela IA (detectado em parts). Motivo: {block_reason_detail}")
                        raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
                    else:
                        self.logger.warning("Resposta da IA (via parts) não contém texto processado ou partes válidas.")
                        raise ValueError("Resposta da IA (via parts) está vazia ou inválida.")

                elif hasattr(response, "text") and response.text:
                    self.logger.info("Resposta da IA processada com sucesso (via response.text).")
                    return response.text

                elif (
                    response.prompt_feedback
                    and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED"
                ):
                    block_reason_detail = (
                        response.prompt_feedback.block_reason_message
                        or str(response.prompt_feedback.block_reason)
                    )
                    self.logger.warning(f"Conteúdo bloqueado pela IA (sem partes/texto, mas com feedback). Motivo: {block_reason_detail}")
                    raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
                else:
                    self.logger.warning("Resposta da API Gemini não contém 'text', 'parts' válidas ou feedback de bloqueio claro.")
                    raise ValueError("Resposta da API Gemini está em formato inesperado ou vazia.")
            except Exception as e:
                self.logger.error(f"Erro ao tentar GOOGLE_API_KEY_{idx}: {e}", exc_info=True)
                last_exception = e
                continue
        
        # Se chegou aqui, todas as tentativas falharam
        if last_exception:
            raise RuntimeError(f"Todas as APIs Gemini falharam. Último erro: {last_exception}")
        else:
            raise RuntimeError("Nenhuma API Key Gemini configurada. Configure GOOGLE_API_KEY_1 ou GOOGLE_API_KEY_2 no .env")
