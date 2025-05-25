# app/services/report_service.py
import logging
import os
import google.generativeai as genai
from flask import current_app

class ReportService:
    """
    Serviço responsável por interagir com a API de IA Generativa do Google
    para processar relatórios de segurança patrimonial.
    """
    def __init__(self,
                 prompt_template_filename="patrimonial_security_report_template.txt",
                 email_prompt_template_filename="email_professional_format_template.txt"): # Novo prompt
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._prompt_template_content = None
        self._email_prompt_template_content = None # Para o novo prompt
        self._google_api_key = None

        try:
            self._google_api_key = os.getenv('GOOGLE_API_KEY')
            if not self._google_api_key:
                self.logger.error("API Key do Google (GOOGLE_API_KEY) não encontrada nas variáveis de ambiente.")
                raise ValueError("API Key do Google não configurada.")

            genai.configure(api_key=self._google_api_key)
            self.logger.info("Configuração da API Key do Google bem-sucedida.")

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
                model_name="gemini-1.5-flash-latest",
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            self.logger.info(f"ReportService: Modelo Gemini '{self.model.model_name}' inicializado com sucesso.")

        except ValueError as ve:
            self.logger.critical(f"Falha na inicialização do ReportService (configuração da API): {ve}")
        except Exception as e:
            self.logger.critical(f"Falha catastrófica na inicialização do ReportService: {e}", exc_info=True)

        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Carregar template padrão
        template_path = os.path.join(current_dir, "prompt_templates", prompt_template_filename)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self._prompt_template_content = f.read()
            self.logger.info(f"Template de prompt padrão '{prompt_template_filename}' carregado de '{template_path}'.")
        except FileNotFoundError:
            self.logger.error(f"Arquivo de template de prompt padrão não encontrado: {template_path}")
            self._prompt_template_content = None
        except Exception as e:
            self.logger.error(f"Erro ao carregar o template de prompt padrão '{template_path}': {e}", exc_info=True)
            self._prompt_template_content = None

        # Carregar template de email
        email_template_path = os.path.join(current_dir, "prompt_templates", email_prompt_template_filename)
        try:
            with open(email_template_path, 'r', encoding='utf-8') as f:
                self._email_prompt_template_content = f.read()
            self.logger.info(f"Template de prompt de email '{email_prompt_template_filename}' carregado de '{email_template_path}'.")
        except FileNotFoundError:
            self.logger.warning(f"Arquivo de template de prompt de email não encontrado: {email_template_path}. A formatação de email não funcionará.")
            self._email_prompt_template_content = None
        except Exception as e:
            self.logger.error(f"Erro ao carregar o template de prompt de email '{email_template_path}': {e}", exc_info=True)
            self._email_prompt_template_content = None


    def _construir_prompt(self, dados_brutos: str, prompt_type: str = "standard") -> str:
        template_content_to_use = None
        if prompt_type == "email":
            template_content_to_use = self._email_prompt_template_content
            if not template_content_to_use:
                self.logger.error("Template de prompt de email não carregado ou vazio ao tentar construir o prompt de email.")
                raise ValueError("Template de prompt de email não está disponível.")
        else: # Padrão é "standard"
            template_content_to_use = self._prompt_template_content
            if not template_content_to_use:
                self.logger.error("Template de prompt padrão não carregado ou vazio ao tentar construir o prompt.")
                raise ValueError("Template de prompt padrão não está disponível.")

        self.logger.debug(f"Construindo prompt (tipo: {prompt_type}). Chave esperada no template via .format(): {{dados_brutos}}.")

        try:
            prompt_completo = template_content_to_use.format(dados_brutos=dados_brutos)
            return prompt_completo
        except KeyError as e:
            self.logger.error(
                f"KeyError ao formatar o prompt (tipo: {prompt_type}): A chave '{e}' não foi encontrada. "
                f"Verifique se o template contém EXATAMENTE '{{dados_brutos}}'."
            )
            raise ValueError(f"Erro ao construir o prompt (tipo: {prompt_type}): placeholder para a chave '{e}' está inválido ou ausente no template.")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao formatar o prompt (tipo: {prompt_type}): {e}", exc_info=True)
            raise ValueError(f"Erro inesperado ao formatar o prompt (tipo: {prompt_type}): {str(e)}")


    def processar_relatorio_com_ia(self, relatorio_bruto: str, prompt_type: str = "standard") -> str: # Adicionado prompt_type
        if self.model is None:
            self.logger.error("Modelo de IA não inicializado. Não é possível processar.")
            raise RuntimeError("Serviço de IA não está configurado corretamente.")

        if prompt_type == "email" and not self._email_prompt_template_content:
            self.logger.error("Processamento de email solicitado, mas o template de email não foi carregado.")
            raise RuntimeError("Template de prompt de email não configurado corretamente.")
        elif prompt_type == "standard" and not self._prompt_template_content:
            self.logger.error("Processamento padrão solicitado, mas o template padrão não foi carregado.")
            raise RuntimeError("Template de prompt padrão não configurado corretamente.")


        if not isinstance(relatorio_bruto, str):
            self.logger.warning("Entrada 'relatorio_bruto' não é uma string.")
            raise ValueError("'relatorio_bruto' deve ser uma string.")
        if not relatorio_bruto.strip():
            self.logger.warning("Entrada 'relatorio_bruto' está vazia.")
            raise ValueError("'relatorio_bruto' não pode estar vazio.")

        try:
            prompt_final = self._construir_prompt(relatorio_bruto, prompt_type=prompt_type) # Passa prompt_type
            self.logger.info(f"Enviando prompt (tipo: {prompt_type}) para o modelo Gemini (primeiros 100 chars): {prompt_final[:100]}...")

            response = self.model.generate_content(prompt_final)

            self.logger.debug(f"Resposta bruta da API Gemini: {response}")
            # ... ( restante do tratamento da resposta, como já existe) ...
            if hasattr(response, 'text') and response.text:
                self.logger.info(f"Relatório (tipo: {prompt_type}) processado pela IA com sucesso (usando response.text).")
                return response.text
            elif response.parts:
                texto_processado = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                if not texto_processado and response.prompt_feedback and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED":
                    block_reason_detail = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
                    self.logger.warning(f"Conteúdo bloqueado pela IA (tipo: {prompt_type}). Motivo: {block_reason_detail}")
                    raise ValueError(f"O conteúdo gerado (tipo: {prompt_type}) foi bloqueado pela IA. Motivo: {block_reason_detail}")
                elif not texto_processado:
                    self.logger.warning(f"Resposta da IA (tipo: {prompt_type}) não contém texto processado ou partes válidas (após processar 'parts').")
                    raise ValueError(f"Resposta da IA (tipo: {prompt_type}) está vazia ou inválida (após processar 'parts').")

                self.logger.info(f"Relatório (tipo: {prompt_type}) processado pela IA com sucesso (usando response.parts).")
                return texto_processado
            elif response.prompt_feedback and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED":
                 block_reason_detail = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
                 self.logger.warning(f"Conteúdo bloqueado pela IA (tipo: {prompt_type}) (sem partes, mas com feedback). Motivo: {block_reason_detail}")
                 raise ValueError(f"O conteúdo gerado (tipo: {prompt_type}) foi bloqueado pela IA. Motivo: {block_reason_detail}")
            else:
                self.logger.warning(f"Resposta da IA (tipo: {prompt_type}) não contém 'text', 'parts' válidas ou feedback de bloqueio claro.")
                raise ValueError(f"Resposta da API Gemini (tipo: {prompt_type}) está em formato inesperado ou vazia.")

        except ValueError as ve:
            self.logger.error(f"Erro de valor durante o processamento com IA (tipo: {prompt_type}): {ve}")
            raise
        except genai.types.BlockedPromptException as bpe:
            self.logger.warning(f"Prompt (tipo: {prompt_type}) bloqueado pela API Gemini: {bpe}")
            raise ValueError(f"Seu prompt (tipo: {prompt_type}) foi bloqueado por razões de segurança: {bpe}")
        except genai.types.StopCandidateException as sce:
            self.logger.warning(f"Geração (tipo: {prompt_type}) interrompida pela API Gemini: {sce}")
            raise ValueError(f"A geração de conteúdo (tipo: {prompt_type}) foi interrompida: {sce}")
        except Exception as e:
            self.logger.error(f"Erro inesperado durante a comunicação com a API Gemini (tipo: {prompt_type}): {e}", exc_info=True)
            if isinstance(getattr(e, 'response', None), str) and e.response.strip().lower().startswith("<!doctype html"):
                 self.logger.error("A exceção da API Gemini continha uma resposta HTML.")
                 raise RuntimeError("Falha na comunicação com a API Gemini: resposta inesperada em formato HTML na exceção.")
            raise RuntimeError(f"Erro de comunicação com o serviço de IA (tipo: {prompt_type}): {str(e)}")