# app/services/consolidated_report_service.py
import os
from jinja2 import Environment, FileSystemLoader

from .base_generative_service import BaseGenerativeService

class ConsolidatedReportService(BaseGenerativeService):
    def __init__(
        self,
        model_name="gemini-2.5-flash",
        template_filename="daily_consolidated_report_template.txt",
    ):
        super().__init__(model_name=model_name)
        self._template = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "prompt_templates")

            jinja_env = Environment(
                loader=FileSystemLoader(template_folder),
            )
            self._template = jinja_env.get_template(template_filename)
            self.logger.info(
                f"Template '{template_filename}' carregado para ConsolidatedReportService."
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao carregar template '{template_filename}' para ConsolidatedReportService: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Falha ao carregar template para ConsolidatedReportService: {e}"
            ) from e

    def gerar_relatorio_consolidado(self, dados_brutos: str) -> str:
        """
        Gera um relatório consolidado diário processado pela IA Gemini
        usando um template específico.
        """
        self.logger.info("Iniciando geração de relatório consolidado.")

        if self.client is None:
            raise RuntimeError("Serviço de IA não configurado corretamente.")

        if not self._template:
            raise RuntimeError("Template não carregado.")

        try:
            prompt_para_ia = self._template.render(dados_brutos=dados_brutos)
            texto_processado = self._call_generative_model(prompt_para_ia)

            self.logger.info("Relatório consolidado gerado com sucesso.")
            return texto_processado
        except Exception as e:
            self.logger.exception("Erro inesperado ao gerar relatório consolidado.")
            raise RuntimeError(f"Erro no serviço de relatório: {str(e)}") from e
