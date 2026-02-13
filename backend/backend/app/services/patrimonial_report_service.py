# app/services/patrimonial_report_service.py
import os

from jinja2 import Environment, FileSystemLoader  # Para carregar o template

from .base_generative_service import \
    BaseGenerativeService  # Importa a classe base


class PatrimonialReportService(BaseGenerativeService):
    def __init__(
        self,
        model_name="gemini-2.5-flash",
        template_filename="patrimonial_security_report_template.txt",
    ):
        super().__init__(
            model_name=model_name
        )  # Chama o construtor da BaseGenerativeService
        # self.logger já é inicializado na BaseGenerativeService com o nome desta classe.
        self._template = None
        try:
            # Obtém o diretório atual do arquivo de serviço
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Constrói o caminho para a pasta de templates de prompt
            template_folder = os.path.join(current_dir, "prompt_templates")

            jinja_env = Environment(
                loader=FileSystemLoader(template_folder),
                autoescape=True,  # Boa prática para templates, embora este seja texto.
            )
            self._template = jinja_env.get_template(template_filename)
            self.logger.info(
                f"Template '{template_filename}' carregado para PatrimonialReportService."
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao carregar template '{template_filename}' para PatrimonialReportService: {e}",
                exc_info=True,
            )
            # Decide como tratar o erro. Relançar é uma boa opção para indicar que o serviço não está funcional.
            raise RuntimeError(
                f"Falha ao carregar template para PatrimonialReportService: {e}"
            ) from e

    def _construir_prompt_relatorio_patrimonial(self, dados_brutos: str) -> str:
        if not self._template:
            self.logger.error(
                "Tentativa de construir prompt, mas o template não foi carregado."
            )
            raise RuntimeError("Template de relatório patrimonial não está carregado.")

        if not isinstance(dados_brutos, str):
            self.logger.warning("dados_brutos não é uma string.")
            # Considerar se isso deve ser um erro mais específico ou tratado antes.
            raise ValueError(
                "Os dados brutos para o relatório devem ser fornecidos como uma string."
            )

        try:
            # O template 'patrimonial_security_report_template.txt' espera um placeholder {dados_brutos}
            prompt_final = self._template.render(dados_brutos=dados_brutos)
            self.logger.debug(
                f"Prompt para Relatório Patrimonial (primeiros 100 chars): {prompt_final[:100]}..."
            )
            return prompt_final
        except Exception as e:
            self.logger.error(
                f"Erro ao renderizar template de relatório patrimonial com Jinja2: {e}",
                exc_info=True,
            )
            raise ValueError(
                f"Erro ao construir o prompt para o relatório patrimonial: {str(e)}"
            ) from e

    def gerar_relatorio_seguranca(self, dados_brutos_relatorio: str) -> str:
        """
        Gera um relatório de segurança patrimonial processado pela IA Gemini
        usando um template de prompt.
        """
        self.logger.info(
            f"Iniciando geração de relatório de segurança para dados brutos (primeiros 70 chars): '{dados_brutos_relatorio[:70]}...'"
        )

        if self.client is None:  # Verificação herdada da BaseGenerativeService
            self.logger.error(
                "Cliente de IA não inicializado no PatrimonialReportService."
            )
            raise RuntimeError(
                "Serviço de IA não configurado corretamente (cliente não inicializado)."
            )

        try:
            prompt_para_ia = self._construir_prompt_relatorio_patrimonial(
                dados_brutos_relatorio
            )

            # Chama o método da classe base para interagir com o modelo Gemini
            texto_processado = self._call_generative_model(prompt_para_ia)

            self.logger.info(
                "Relatório de segurança patrimonial gerado pela IA com sucesso."
            )
            return texto_processado
        except (
            ValueError
        ) as ve:  # Captura erros de validação de dados ou problemas com o template
            self.logger.error(f"Erro de valor ao gerar relatório de segurança: {ve}")
            raise  # Relança para a rota tratar e informar o usuário
        except (
            RuntimeError
        ) as rte:  # Captura erros de configuração ou da chamada da IA na base
            self.logger.error(f"Erro de runtime ao gerar relatório de segurança: {rte}")
            raise  # Relança
        except Exception as e:
            # Usar self.logger.exception para incluir o traceback automaticamente no log
            self.logger.exception(
                "Erro inesperado ao gerar relatório de segurança patrimonial."
            )
            # Para erros não esperados, você pode querer uma exceção mais genérica ou específica do seu app
            raise RuntimeError(
                f"Erro inesperado no serviço de relatório patrimonial: {str(e)}"
            ) from e
