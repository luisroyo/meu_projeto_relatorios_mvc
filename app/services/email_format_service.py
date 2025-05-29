# app/services/email_format_service.py
import logging
import os
from .base_generative_service import BaseGenerativeService # Importa a classe base

class EmailFormatService(BaseGenerativeService):
    def __init__(self):
        super().__init__() # Chama o construtor da classe base
        self.logger = logging.getLogger(__name__) 
        self._template_content = None
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Ajuste o caminho se a pasta prompt_templates estiver em outro lugar
            template_path = os.path.join(current_dir, "prompt_templates", "email_professional_format_template.txt")
            with open(template_path, 'r', encoding='utf-8') as f:
                self._template_content = f.read()
            self.logger.info("Template 'email_professional_format_template.txt' carregado.")
        except Exception as e:
            self.logger.error(f"Erro ao carregar template de formatação de email: {e}", exc_info=True)
            self._template_content = None

    def formatar_para_email(self, texto_original: str) -> str:
        if not self._template_content:
            self.logger.error("Tentativa de formatar para email, mas o template não foi carregado.")
            raise RuntimeError("Template de formatação de email não está carregado ou não foi encontrado.")

        if not isinstance(texto_original, str):
            self.logger.warning("texto_original não é uma string para formatar_para_email.")
            raise ValueError("texto_original deve ser uma string.")

        try:
            # Verifique qual placeholder seu email_professional_format_template.txt usa.
            # Se for {{ texto_original }}, você precisará usar Jinja2 como no JustificativaAtestadoService.
            # Se for {texto_original} ou {dados_brutos}, .format() pode funcionar.
            # Vou assumir que é {texto_original} para este exemplo com .format():
            prompt_final = self._template_content.format(texto_original=texto_original)
            # Se seu template de email for mais complexo e usar {{ ... }}, você precisará
            # carregar e renderizar com Jinja2, similar ao JustificativaAtestadoService.
        except KeyError as e:
            self.logger.error(f"Placeholder não encontrado no template de email. Chave esperada: {e}")
            raise ValueError(f"Erro ao construir prompt de email: placeholder {e} ausente.")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao formatar o prompt de email: {e}", exc_info=True)
            raise ValueError(f"Erro inesperado ao formatar o prompt de email: {str(e)}")

        return self._call_generative_model(prompt_final)