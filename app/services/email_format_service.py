# app/services/email_format_service.py
import os

from jinja2 import Environment, FileSystemLoader  # Adicionado Jinja2

from .base_generative_service import BaseGenerativeService


class EmailFormatService(BaseGenerativeService):
    def __init__(
        self,
        model_name="gemini-1.5-flash-latest",
        template_filename="email_professional_format_template.txt",
    ):
        super().__init__(model_name=model_name)
        # self.logger já é inicializado pela BaseGenerativeService
        self._template = (
            None  # Alterado para _template para armazenar o objeto template Jinja2
        )
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "prompt_templates")
            jinja_env = Environment(
                loader=FileSystemLoader(template_folder), autoescape=True
            )
            self._template = jinja_env.get_template(template_filename)
            self.logger.info(
                f"Template '{template_filename}' carregado para EmailFormatService."
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao carregar template '{template_filename}' para EmailFormatService: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Falha ao carregar template para EmailFormatService: {e}"
            ) from e

    def _construir_prompt_formatacao_email(self, dados_brutos_email: str) -> str:
        if not self._template:
            self.logger.error(
                "Tentativa de construir prompt de email, mas o template não foi carregado."
            )
            raise RuntimeError("Template de formatação de email não está carregado.")

        if not isinstance(dados_brutos_email, str):
            self.logger.warning("dados_brutos_email não é uma string.")
            raise ValueError(
                "Os dados brutos para o email devem ser fornecidos como uma string."
            )

        try:
            # O template 'email_professional_format_template.txt' espera {dados_brutos}
            # Usando Jinja2 para renderizar:
            prompt_final = self._template.render(dados_brutos=dados_brutos_email)
            self.logger.debug(
                f"Prompt para Formatação de Email (100 chars): {prompt_final[:100]}..."
            )
            return prompt_final
        except Exception as e:  # Captura erros de renderização do Jinja2 também
            self.logger.error(
                f"Erro ao renderizar template de formatação de email com Jinja2: {e}",
                exc_info=True,
            )
            raise ValueError(
                f"Erro ao construir o prompt para formatação de email: {str(e)}"
            ) from e

    def formatar_para_email(self, texto_original_relatorio: str) -> str:
        """
        Formata um texto de relatório (potencialmente já processado) para um formato de email
        usando IA Gemini e um template de prompt.
        """
        self.logger.info(
            f"Iniciando formatação para email do texto (primeiros 70 chars): '{texto_original_relatorio[:70]}...'"
        )

        if self.model is None:
            self.logger.error("Modelo de IA não inicializado no EmailFormatService.")
            raise RuntimeError(
                "Serviço de IA não configurado corretamente (modelo não inicializado)."
            )

        try:
            prompt_para_ia = self._construir_prompt_formatacao_email(
                texto_original_relatorio
            )

            texto_formatado_email = self._call_generative_model(prompt_para_ia)

            self.logger.info("Texto formatado para email pela IA com sucesso.")
            return texto_formatado_email
        except ValueError as ve:
            self.logger.error(f"Erro de valor ao formatar para email: {ve}")
            raise
        except RuntimeError as rte:
            self.logger.error(f"Erro de runtime ao formatar para email: {rte}")
            raise
        except Exception as e:
            self.logger.exception("Erro inesperado ao formatar para email:")
            raise RuntimeError(
                f"Erro inesperado no serviço de formatação de email: {str(e)}"
            ) from e
