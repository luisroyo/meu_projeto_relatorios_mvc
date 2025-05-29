# app/services/justificativa_service.py
import logging # Adicionado para consistência, embora o logger seja herdado
import os
from jinja2 import Environment, FileSystemLoader # pip install Jinja2
from .base_generative_service import BaseGenerativeService 

class JustificativaAtestadoService(BaseGenerativeService):
    def __init__(self):
        super().__init__() 
        # self.logger já é inicializado na BaseGenerativeService com o nome desta classe.
        # Se você quiser um logger com o nome 'app.services.justificativa_service' especificamente:
        # self.logger = logging.getLogger(__name__)
        self._template = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_folder = os.path.join(current_dir, "prompt_templates")
            jinja_env = Environment(
                loader=FileSystemLoader(template_folder),
                autoescape=True 
            )
            self._template = jinja_env.get_template("justificativa_atestado_medico_template.txt")
            self.logger.info("Template 'justificativa_atestado_medico_template.txt' carregado.") # Logger da base será usado
        except Exception as e:
            self.logger.error(f"Erro ao carregar template de justificativa: {e}", exc_info=True)
            # É importante decidir como tratar este erro. Relançar é uma opção.
            # Se relançar, a instanciação do serviço falhará, o que pode ser o desejado.
            raise RuntimeError(f"Falha ao carregar template para JustificativaAtestadoService: {e}") from e

    def gerar_justificativa(self, dados_justificativa: dict) -> str:
        if not self._template:
            # Este erro ocorreria se o __init__ falhasse em carregar o template mas não relançasse a exceção.
            self.logger.error("Tentativa de gerar justificativa, mas o template não foi carregado.")
            raise RuntimeError("Template de justificativa de atestado não está carregado.")
        
        if not isinstance(dados_justificativa, dict):
            self.logger.warning("dados_justificativa não é um dicionário.")
            raise ValueError("Os dados para a justificativa devem ser fornecidos como um dicionário.")

        try:
            prompt_final = self._template.render(dados_justificativa)
            self.logger.debug(f"Prompt para JustificativaAtestado (100 chars): {prompt_final[:100]}")
        except Exception as e:
            self.logger.error(f"Erro ao renderizar template de justificativa com Jinja2: {e}", exc_info=True)
            raise ValueError(f"Erro ao construir o prompt para a justificativa: {str(e)}") from e
            
        return self._call_generative_model(prompt_final)