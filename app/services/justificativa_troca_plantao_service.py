# app/services/justificativa_troca_plantao_service.py
import logging
import os
from .base_generative_service import BaseGenerativeService
from jinja2 import Environment, FileSystemLoader

class JustificativaTrocaPlantaoService(BaseGenerativeService):
    def __init__(self, model_name="gemini-1.5-flash-latest", template_filename="justificativa_troca_plantao_template.txt"):
        super().__init__(model_name=model_name)
        self._template = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "prompt_templates")
            jinja_env = Environment(loader=FileSystemLoader(template_folder), autoescape=True)
            self._template = jinja_env.get_template(template_filename)
            self.logger.info(f"Template '{template_filename}' carregado para JustificativaTrocaPlantaoService.")
        except Exception as e:
            self.logger.error(f"Erro ao carregar template '{template_filename}' para JustificativaTrocaPlantaoService: {e}", exc_info=True)
            raise RuntimeError(f"Falha ao carregar template para JustificativaTrocaPlantaoService: {e}") from e

    def _construir_prompt(self, dados_justificativa: dict) -> str:
        if not self._template:
            raise RuntimeError("Template de justificativa de troca de plantão não está carregado.")
        if not isinstance(dados_justificativa, dict):
            raise ValueError("Os dados para a justificativa de troca de plantão devem ser um dicionário.")
        try:
            # O template 'justificativa_troca_plantao_template.txt' espera placeholders como {{ colaborador_a_nome }}
            prompt_final = self._template.render(dados_justificativa) # Passa o dicionário diretamente
            self.logger.debug(f"Prompt para JustificativaTrocaPlantao (100 chars): {prompt_final[:100]}...")
            return prompt_final
        except Exception as e:
            self.logger.error(f"Erro ao renderizar template de justificativa de troca com Jinja2: {e}", exc_info=True)
            raise ValueError(f"Erro ao construir o prompt para a justificativa de troca: {str(e)}") from e

    def gerar_justificativa_troca(self, dados_justificativa: dict) -> str:
        self.logger.info(f"Gerando justificativa de troca de plantão com dados: {dados_justificativa}")
        if self.model is None:
            raise RuntimeError("Serviço de IA não configurado corretamente (modelo não inicializado).")
        try:
            prompt = self._construir_prompt(dados_justificativa)
            texto_gerado = self._call_generative_model(prompt)
            self.logger.info("Justificativa de troca de plantão gerada com sucesso.")
            return texto_gerado
        except ValueError as ve:
            self.logger.error(f"Erro de valor ao gerar justificativa de troca: {ve}")
            raise
        except RuntimeError as rte:
            self.logger.error(f"Erro de runtime ao gerar justificativa de troca: {rte}")
            raise
        except Exception as e:
            self.logger.exception("Erro inesperado ao gerar justificativa de troca de plantão:")
            raise RuntimeError(f"Erro inesperado no serviço de justificativa de troca: {str(e)}") from e