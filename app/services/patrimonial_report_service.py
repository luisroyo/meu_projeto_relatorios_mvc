# app/services/patrimonial_report_service.py
import logging
import os
from .base_generative_service import BaseGenerativeService # Importa a classe base

class PatrimonialReportService(BaseGenerativeService):
    def __init__(self):
        super().__init__() # Chama o construtor da classe base
        self.logger = logging.getLogger(__name__) # Ou use o self.logger herdado se já configurado na base
        self._template_content = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Ajuste este caminho se necessário para encontrar seus templates
            template_path = os.path.join(current_dir, "prompt_templates", "patrimonial_security_report_template.txt")
            with open(template_path, 'r', encoding='utf-8') as f:
                self._template_content = f.read()
            self.logger.info("Template 'patrimonial_security_report_template.txt' carregado.")
        except Exception as e:
            self.logger.error(f"Erro ao carregar template patrimonial: {e}", exc_info=True)
            self._template_content = None # Importante para verificações posteriores

    def gerar_relatorio_seguranca(self, dados_brutos: str) -> str:
        if not self._template_content:
            self.logger.error("Tentativa de gerar relatório de segurança, mas o template não foi carregado.")
            raise RuntimeError("Template de relatório de segurança não está carregado ou não foi encontrado.")

        if not isinstance(dados_brutos, str): # Validação básica
            self.logger.warning("dados_brutos não é uma string para gerar_relatorio_seguranca.")
            raise ValueError("dados_brutos deve ser uma string.")

        try:
            # Assumindo que o template patrimonial_security_report_template.txt usa {dados_brutos}
            prompt_final = self._template_content.format(dados_brutos=dados_brutos)
        except KeyError:
            self.logger.error("Placeholder {dados_brutos} não encontrado no template patrimonial.")
            raise ValueError("Erro ao construir prompt patrimonial: placeholder {dados_brutos} ausente no template.")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao formatar o prompt patrimonial: {e}", exc_info=True)
            raise ValueError(f"Erro inesperado ao formatar o prompt patrimonial: {str(e)}")

        # Chama o método da classe base para interagir com o modelo Gemini
        return self._call_generative_model(prompt_final)