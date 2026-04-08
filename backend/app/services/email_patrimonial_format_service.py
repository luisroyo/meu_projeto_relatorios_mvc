import os

from jinja2 import Environment, FileSystemLoader

from .base_generative_service import BaseGenerativeService


class EmailPatrimonialFormatService(BaseGenerativeService):
    def __init__(
        self,
        model_name="gemini-2.5-flash",
        template_filename="email_patrimonial_format_template.txt",
    ):
        super().__init__(model_name=model_name)
        self._template = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "prompt_templates")
            jinja_env = Environment(
                loader=FileSystemLoader(template_folder), autoescape=True
            )
            self._template_padrao = jinja_env.get_template("email_patrimonial_format_template.txt")
            self._template_consolidado = jinja_env.get_template("email_consolidado_format_template.txt")
            self.logger.info("Templates de formatação carregados para EmailPatrimonialFormatService.")
        except Exception as e:
            self.logger.error(
                f"Erro ao carregar template '{template_filename}' para EmailPatrimonialFormatService: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Falha ao carregar template para EmailPatrimonialFormatService: {e}"
            ) from e

    def _construir_prompt(self, dados_brutos: str, consolidado=False) -> str:
        template = self._template_consolidado if consolidado else self._template_padrao
        
        if not template:
            raise RuntimeError("Template de formatação não está carregado.")

        if not isinstance(dados_brutos, str):
            raise ValueError("Os dados brutos devem ser uma string.")

        try:
            return template.render(dados_brutos=dados_brutos)
        except Exception as e:
            self.logger.error(f"Erro ao renderizar template: {e}", exc_info=True)
            raise ValueError(f"Erro ao construir o prompt: {str(e)}") from e

    def formatar_email_patrimonial(self, texto_relatorio: str) -> str:
        """
        Formata o relatório patrimonial final em um padrão de e-mail 
        usando a IA e o template dedicado.
        """
        self.logger.info("Iniciando formatação do e-mail patrimonial.")

        if self.client is None:
            raise RuntimeError("Serviço de IA não configurado corretamente.")

        try:
            prompt_para_ia = self._construir_prompt(texto_relatorio, consolidado=False)
            texto_formatado = self._call_generative_model(prompt_para_ia)
            self.logger.info("E-mail formatado pela IA com sucesso.")
            return texto_formatado
        except Exception as e:
            self.logger.exception("Erro inesperado ao formatar e-mail patrimonial:")
            raise RuntimeError(f"Erro inesperado no serviço de IA: {str(e)}") from e

    def formatar_email_consolidado(self, texto_relatorios: str) -> str:
        """
        Formata MÚLTIPLOS relatórios patrimoniais em um único e-mail
        """
        self.logger.info("Iniciando formatação de E-mail Consolidado.")

        if self.client is None:
            raise RuntimeError("Serviço de IA não configurado corretamente.")

        try:
            prompt_para_ia = self._construir_prompt(texto_relatorios, consolidado=True)
            texto_formatado = self._call_generative_model(prompt_para_ia)
            self.logger.info("E-mail múltiplo formatado pela IA com sucesso.")
            return texto_formatado
        except Exception as e:
            self.logger.exception("Erro inesperado ao consolidar e-mails:")
            raise RuntimeError(f"Erro inesperado no serviço de IA: {str(e)}") from e
