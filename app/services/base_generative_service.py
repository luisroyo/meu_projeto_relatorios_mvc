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
            self._google_api_key = os.getenv("GOOGLE_API_KEY")
            if not self._google_api_key:
                self.logger.error(
                    "API Key do Google (GOOGLE_API_KEY) não encontrada nas variáveis de ambiente."
                )
                raise RuntimeError(
                    "API Key do Google (GOOGLE_API_KEY) não configurada nas variáveis de ambiente."
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
        if self.model is None:
            self.logger.error(
                "Modelo de IA não inicializado. Não é possível processar."
            )
            raise RuntimeError(
                "Serviço de IA não está configurado corretamente (modelo não inicializado)."
            )

        if not isinstance(prompt_final, str) or not prompt_final.strip():
            self.logger.warning("Prompt final está vazio ou não é uma string.")
            raise ValueError("Prompt final para a IA não pode ser vazio.")

        try:
            # A lógica de log aqui dentro só será executada se a chamada não estiver em cache.
            self.logger.info(
                f"CACHE MISS. Enviando novo prompt para o modelo Gemini (primeiros 100 chars): {prompt_final[:100]}..."
            )
            response = self.model.generate_content(prompt_final)
            self.logger.debug(f"Resposta bruta da API Gemini: {response}")

            if response.parts:
                texto_processado = "".join(
                    part.text for part in response.parts if hasattr(part, "text")
                )
                if texto_processado:
                    self.logger.info(
                        "Resposta da IA processada com sucesso (via response.parts)."
                    )
                    return texto_processado
                elif (
                    response.prompt_feedback
                    and str(response.prompt_feedback.block_reason)
                    != "BLOCK_REASON_UNSPECIFIED"
                ):
                    block_reason_detail = (
                        response.prompt_feedback.block_reason_message
                        or str(response.prompt_feedback.block_reason)
                    )
                    self.logger.warning(
                        f"Conteúdo bloqueado pela IA (detectado em parts). Motivo: {block_reason_detail}"
                    )
                    raise ValueError(
                        f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}"
                    )
                else:
                    self.logger.warning(
                        "Resposta da IA (via parts) não contém texto processado ou partes válidas."
                    )
                    raise ValueError(
                        "Resposta da IA (via parts) está vazia ou inválida."
                    )

            elif hasattr(response, "text") and response.text:
                self.logger.info(
                    "Resposta da IA processada com sucesso (via response.text)."
                )
                return response.text

            elif (
                response.prompt_feedback
                and str(response.prompt_feedback.block_reason)
                != "BLOCK_REASON_UNSPECIFIED"
            ):
                block_reason_detail = (
                    response.prompt_feedback.block_reason_message
                    or str(response.prompt_feedback.block_reason)
                )
                self.logger.warning(
                    f"Conteúdo bloqueado pela IA (sem partes/texto, mas com feedback). Motivo: {block_reason_detail}"
                )
                raise ValueError(
                    f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}"
                )
            else:
                self.logger.warning(
                    "Resposta da API Gemini não contém 'text', 'parts' válidas ou feedback de bloqueio claro."
                )
                raise ValueError(
                    "Resposta da API Gemini está em formato inesperado ou vazia."
                )

        except ValueError as ve:
            self.logger.error(f"Erro de valor durante o processamento com IA: {ve}")
            raise
        except genai.types.BlockedPromptException as bpe:
            self.logger.warning(f"Prompt bloqueado pela API Gemini: {bpe}")
            raise ValueError(
                f"Seu prompt foi bloqueado por razões de segurança: {bpe}"
            ) from bpe
        except genai.types.StopCandidateException as sce:
            self.logger.warning(f"Geração interrompida pela API Gemini: {sce}")
            raise ValueError(f"A geração de conteúdo foi interrompida: {sce}") from sce
        except Exception as e:
            self.logger.error(
                f"Erro inesperado durante a comunicação com a API Gemini: {e}",
                exc_info=True,
            )
            if isinstance(
                getattr(e, "response", None), str
            ) and e.response.strip().lower().startswith("<!doctype html"):
                self.logger.error("A exceção da API Gemini continha uma resposta HTML.")
                raise RuntimeError(
                    "Falha na comunicação com a API Gemini: resposta inesperada em formato HTML na exceção."
                ) from e
            raise RuntimeError(
                f"Erro de comunicação com o serviço de IA: {str(e)}"
            ) from e
