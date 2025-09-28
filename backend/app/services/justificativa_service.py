# app/services/justificativa_service.py
import os

from jinja2 import Environment, FileSystemLoader

from .base_generative_service import BaseGenerativeService


class JustificativaAtestadoService(BaseGenerativeService):
    def __init__(
        self,
        model_name="gemini-2.5-flash",
        template_filename="justificativa_atestado_medico_template.txt",
    ):
        super().__init__(model_name=model_name)
        self._template = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "prompt_templates")
            jinja_env = Environment(
                loader=FileSystemLoader(template_folder), autoescape=True
            )
            self._template = jinja_env.get_template(template_filename)
            self.logger.info(
                f"Template '{template_filename}' carregado para JustificativaAtestadoService."
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao carregar template '{template_filename}' para JustificativaAtestadoService: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Falha ao carregar template para JustificativaAtestadoService: {e}"
            ) from e

    def _construir_prompt(self, dados_justificativa: dict) -> str:
        if not self._template:
            raise RuntimeError(
                "Template de justificativa de atestado não está carregado."
            )
        if not isinstance(dados_justificativa, dict):
            raise ValueError(
                "Os dados para a justificativa de atestado devem ser um dicionário."
            )
        try:
            prompt_final = self._template.render(dados_justificativa)
            self.logger.debug(
                f"Prompt para JustificativaAtestado (100 chars): {prompt_final[:100]}..."
            )
            return prompt_final
        except Exception as e:
            self.logger.error(
                f"Erro ao renderizar template de justificativa de atestado com Jinja2: {e}",
                exc_info=True,
            )
            raise ValueError(
                f"Erro ao construir o prompt para a justificativa de atestado: {str(e)}"
            ) from e

    def gerar_justificativa(
        self, dados_justificativa: dict
    ) -> str:  # Nome do método corrigido para consistência
        self.logger.info(
            f"Gerando justificativa de atestado com dados: {dados_justificativa}"
        )
        if self.client is None:
            raise RuntimeError(
                "Serviço de IA não configurado corretamente (cliente não inicializado)."
            )
        try:
            prompt = self._construir_prompt(dados_justificativa)
            texto_gerado = self._call_generative_model(prompt)
            self.logger.info("Justificativa de atestado gerada com sucesso.")
            return texto_gerado
        except ValueError as ve:
            self.logger.error(f"Erro de valor ao gerar justificativa de atestado: {ve}")
            raise
        except RuntimeError as rte:
            self.logger.error(
                f"Erro de runtime ao gerar justificativa de atestado: {rte}"
            )
            raise
        except Exception as e:
            self.logger.exception("Erro inesperado ao gerar justificativa de atestado:")
            raise RuntimeError(
                f"Erro inesperado no serviço de justificativa de atestado: {str(e)}"
            ) from e
