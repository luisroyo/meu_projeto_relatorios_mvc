# app/services/base_generative_service.py
import logging
import os
import google.generativeai as genai
# from flask import current_app # Removido, pois o serviço base não deve depender diretamente do Flask current_app

class BaseGenerativeService:
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        # Usar o nome da classe filha real para o logger é uma boa prática
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self._google_api_key = None

        try:
            self._google_api_key = os.getenv('GOOGLE_API_KEY')
            if not self._google_api_key:
                self.logger.error("API Key do Google (GOOGLE_API_KEY) não encontrada nas variáveis de ambiente.")
                # Em vez de ValueError, RuntimeError pode ser mais apropriado para falhas de configuração críticas
                raise RuntimeError("API Key do Google (GOOGLE_API_KEY) não configurada nas variáveis de ambiente.")

            genai.configure(api_key=self._google_api_key)
            self.logger.info("Configuração da API Key do Google bem-sucedida para o serviço.")

            # Configurações do modelo (você pode ajustar ou tornar configurável)
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

            self.model = genai.GenerativeModel(
                model_name=model_name, # Usa o model_name passado ou o padrão
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            self.logger.info(f"Modelo Gemini '{self.model.model_name}' inicializado com sucesso para {self.__class__.__name__}.")

        except RuntimeError as rte: # Captura o RuntimeError da API Key
            self.logger.critical(f"Falha na inicialização do serviço (configuração da API): {rte}")
            raise # Relança para que a aplicação saiba que o serviço não está funcional
        except Exception as e:
            self.logger.critical(f"Falha catastrófica na inicialização do serviço ({self.__class__.__name__}): {e}", exc_info=True)
            # É importante relançar ou definir self.model como None de forma clara
            # para que as tentativas de uso falhem explicitamente.
            self.model = None # Garante que o modelo não seja usado se a inicialização falhar
            raise RuntimeError(f"Falha catastrófica na inicialização do serviço de IA: {e}") from e

    def _call_generative_model(self, prompt_final: str) -> str:
        if self.model is None:
            self.logger.error("Modelo de IA não inicializado. Não é possível processar.")
            # Este erro deve idealmente ser pego durante a instanciação do serviço.
            raise RuntimeError("Serviço de IA não está configurado corretamente (modelo não inicializado).")

        if not isinstance(prompt_final, str) or not prompt_final.strip():
            self.logger.warning("Prompt final está vazio ou não é uma string.")
            # Pode ser melhor levantar um erro aqui também, pois um prompt vazio raramente é útil.
            raise ValueError("Prompt final para a IA não pode ser vazio.")

        try:
            self.logger.info(f"Enviando prompt para o modelo Gemini (primeiros 100 chars): {prompt_final[:100]}...")
            response = self.model.generate_content(prompt_final)
            self.logger.debug(f"Resposta bruta da API Gemini: {response}")

            # Lógica de extração de texto e tratamento de bloqueio
            # (Adaptada do seu report_service.py original)
            if response.parts:
                texto_processado = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                # Verifica se, apesar de ter 'parts', o texto resultante é vazio
                if texto_processado:
                    self.logger.info("Resposta da IA processada com sucesso (via response.parts).")
                    return texto_processado
                # Se texto_processado for vazio, verificamos o motivo do bloqueio
                elif response.prompt_feedback and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED":
                    block_reason_detail = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
                    self.logger.warning(f"Conteúdo bloqueado pela IA (detectado em parts). Motivo: {block_reason_detail}")
                    raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
                else:
                    # Resposta tem 'parts' mas não texto, e não foi explicitamente bloqueada com motivo
                    self.logger.warning("Resposta da IA (via parts) não contém texto processado ou partes válidas.")
                    raise ValueError("Resposta da IA (via parts) está vazia ou inválida.")
            
            # Fallback para response.text se response.parts não existir ou não produzir texto (menos comum com Gemini atual)
            # Alguns modelos/versões podem usar 'text' diretamente.
            elif hasattr(response, 'text') and response.text:
                self.logger.info("Resposta da IA processada com sucesso (via response.text).")
                return response.text
            
            # Se não há 'parts' com texto, nem 'text' direto, mas há um feedback de bloqueio
            elif response.prompt_feedback and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED":
                 block_reason_detail = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
                 self.logger.warning(f"Conteúdo bloqueado pela IA (sem partes/texto, mas com feedback). Motivo: {block_reason_detail}")
                 raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
            else:
                # Nenhum texto útil e nenhum motivo de bloqueio claro
                self.logger.warning("Resposta da API Gemini não contém 'text', 'parts' válidas ou feedback de bloqueio claro.")
                raise ValueError("Resposta da API Gemini está em formato inesperado ou vazia.")

        except ValueError as ve: # Captura ValueErrors levantados acima (bloqueio, resposta vazia)
            self.logger.error(f"Erro de valor durante o processamento com IA: {ve}")
            raise # Relança para a rota tratar
        except genai.types.BlockedPromptException as bpe: # Exceção específica da API
            self.logger.warning(f"Prompt bloqueado pela API Gemini: {bpe}")
            raise ValueError(f"Seu prompt foi bloqueado por razões de segurança: {bpe}") from bpe
        except genai.types.StopCandidateException as sce: # Exceção específica da API
            self.logger.warning(f"Geração interrompida pela API Gemini: {sce}")
            raise ValueError(f"A geração de conteúdo foi interrompida: {sce}") from sce
        except Exception as e:
            self.logger.error(f"Erro inesperado durante a comunicação com a API Gemini: {e}", exc_info=True)
            # Verificação de resposta HTML na exceção (útil para depurar problemas de proxy/firewall)
            if isinstance(getattr(e, 'response', None), str) and e.response.strip().lower().startswith("<!doctype html"):
                 self.logger.error("A exceção da API Gemini continha uma resposta HTML.")
                 raise RuntimeError("Falha na comunicação com a API Gemini: resposta inesperada em formato HTML na exceção.") from e
            raise RuntimeError(f"Erro de comunicação com o serviço de IA: {str(e)}") from e