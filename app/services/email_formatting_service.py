# app/services/email_formatting_service.py
import logging
import os
import openai
import httpx

class EmailFormattingService:
    def __init__(self, email_prompt_template_filename="email_professional_format_template.txt"):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._email_prompt_template_content = None
        self._openai_api_key = None

        try:
            self._openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self._openai_api_key:
                self.logger.error("API Key da OpenAI (OPENAI_API_KEY) não encontrada.")
                raise ValueError("API Key da OpenAI não configurada.")

            # USAR ESTA FORMA, POIS O TESTE ISOLADO MOSTROU QUE FUNCIONA:
            http_client_for_openai = httpx.Client() 

            self.client = openai.OpenAI(
                api_key=self._openai_api_key,
                http_client=http_client_for_openai
            )
            self.logger.info("Cliente OpenAI inicializado com sucesso usando httpx.Client() padrão.")

        except ValueError as ve:
            self.logger.critical(f"Falha na inicialização do EmailFormattingService (configuração OpenAI): {ve}")
        except TypeError as te: 
            self.logger.critical(f"TypeError na inicialização do cliente OpenAI ou HTTPX: {te}", exc_info=True)
        except Exception as e:
            self.logger.critical(f"Falha catastrófica na inicialização do EmailFormattingService (OpenAI): {e}", exc_info=True)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "prompt_templates", email_prompt_template_filename)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self._email_prompt_template_content = f.read()
            self.logger.info(f"Template de prompt de email '{email_prompt_template_filename}' carregado para EmailFormattingService.")
        except FileNotFoundError:
            self.logger.error(f"Arquivo de template de prompt de email não encontrado para EmailFormattingService: {template_path}")
            self._email_prompt_template_content = None
        except Exception as e:
            self.logger.error(f"Erro ao carregar o template de prompt de email para EmailFormattingService: {e}", exc_info=True)
            self._email_prompt_template_content = None
            
    def _construir_prompt_email(self, dados_brutos: str) -> str:
        if not self._email_prompt_template_content:
            self.logger.error("Template de prompt de email não carregado ou vazio.")
            raise ValueError("Template de prompt de email não está disponível.")
        
        try:
            prompt_completo = self._email_prompt_template_content.format(dados_brutos=dados_brutos)
            return prompt_completo
        except KeyError as e:
            self.logger.error(f"KeyError ao formatar o prompt de email: Chave '{e}' não encontrada.")
            raise ValueError(f"Erro ao construir o prompt de email: placeholder para chave '{e}' inválido ou ausente.")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao formatar o prompt de email: {e}", exc_info=True)
            raise ValueError(f"Erro inesperado ao formatar o prompt de email: {str(e)}")

    def formatar_relatorio_para_email(self, relatorio_bruto: str) -> str:
        if self.client is None:
            self.logger.error("Cliente OpenAI não inicializado. Não é possível formatar e-mail.")
            raise RuntimeError("Serviço de formatação de e-mail (OpenAI) não configurado corretamente devido a falha na inicialização.")
        if not self._email_prompt_template_content:
            self.logger.error("Template de prompt de email não carregado. Não é possível formatar.")
            raise RuntimeError("Template de prompt de email não configurado para EmailFormattingService.")

        if not isinstance(relatorio_bruto, str) or not relatorio_bruto.strip():
            self.logger.warning("Entrada 'relatorio_bruto' para formatação de e-mail não é string ou está vazia.")
            raise ValueError("'relatorio_bruto' deve ser uma string não vazia.")

        try:
            prompt_final = self._construir_prompt_email(relatorio_bruto)
            self.logger.info(f"Enviando prompt para formatação de e-mail (OpenAI) (primeiros 100 chars): {prompt_final[:100]}...")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em formatar relatórios de ocorrência para e-mails profissionais."},
                    {"role": "user", "content": prompt_final}
                ],
                temperature=0.5, 
                max_tokens=2000  
            )
            
            self.logger.debug(f"Resposta bruta da API OpenAI: {response}")

            if response.choices and response.choices[0].message and response.choices[0].message.content:
                texto_formatado = response.choices[0].message.content.strip()
                self.logger.info("Relatório formatado para e-mail pela OpenAI com sucesso.")
                return texto_formatado
            else:
                self.logger.warning("Resposta da API OpenAI não contém conteúdo de e-mail esperado.")
                raise ValueError("Resposta da API OpenAI para formatação de e-mail está vazia ou em formato inesperado.")

        except ValueError as ve: 
            self.logger.error(f"Erro de valor durante a formatação de e-mail com OpenAI: {ve}")
            raise 
        except openai.APIError as e: 
            self.logger.error(f"Erro da API OpenAI durante a formatação de e-mail: {e}", exc_info=True)
            raise RuntimeError(f"Erro de comunicação com o serviço de formatação de e-mail (OpenAI): {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro inesperado durante a formatação de e-mail com OpenAI: {e}", exc_info=True)
            raise RuntimeError(f"Erro inesperado no serviço de formatação de e-mail (OpenAI): {str(e)}")
