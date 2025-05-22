import os
import google.generativeai as genai
import logging

# Logger específico para este módulo
logger = logging.getLogger(__name__)

# Constantes de Configuração do Modelo e Prompt
MODEL_NAME = "gemini-1.5-flash-latest"
GENERATION_TEMPERATURE = 0.6
GENERATION_TOP_P = 1
GENERATION_TOP_K = 1
GENERATION_MAX_OUTPUT_TOKENS = 4096

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

PROMPT_TEMPLATE_DIR = "prompt_templates"
PROMPT_TEMPLATE_FILENAME = "patrimonial_security_report_template.txt"
PROMPT_TEMPLATE_VERSION_INFO = "guarda patrimonial v5 - pernoite veículo, acionamento central"


class ReportService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            logger.critical("API Key do Google não configurada no arquivo .env. O serviço não pode operar.")
            raise ValueError("API Key do Google não configurada no arquivo .env. O serviço não pode operar.")

        try:
            genai.configure(api_key=self.api_key)
            logger.info("Configuração da API Key do Google bem-sucedida.")
        except Exception as e:
            logger.critical(f"Erro crítico ao configurar a API Key do Google: {e}", exc_info=True)
            raise ValueError(f"Erro ao configurar a API Key do Google: {e}")

        self.generation_config = {
            "temperature": GENERATION_TEMPERATURE,
            "top_p": GENERATION_TOP_P,
            "top_k": GENERATION_TOP_K,
            "max_output_tokens": GENERATION_MAX_OUTPUT_TOKENS,
        }

        try:
            self.model = genai.GenerativeModel(model_name=MODEL_NAME,
                                              generation_config=self.generation_config,
                                              safety_settings=SAFETY_SETTINGS)
            logger.info(f"ReportService: Modelo Gemini '{MODEL_NAME}' inicializado com sucesso.")
        except Exception as e:
            logger.critical(f"Erro crítico ao inicializar o modelo Gemini: {e}", exc_info=True)
            raise RuntimeError(f"Erro ao inicializar o modelo Gemini: {e}")

        self._prompt_template_content = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Carrega o conteúdo do template de prompt de um arquivo."""
        # Constrói o caminho absoluto para o arquivo de template
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, PROMPT_TEMPLATE_DIR, PROMPT_TEMPLATE_FILENAME)

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip():
                logger.error(f"O arquivo de template de prompt '{template_path}' está vazio.")
                raise ValueError(f"O arquivo de template de prompt '{template_path}' está vazio.")
            logger.info(f"Template de prompt '{PROMPT_TEMPLATE_FILENAME}' (versão: {PROMPT_TEMPLATE_VERSION_INFO}) carregado com sucesso de '{template_path}'.")
            return content
        except FileNotFoundError:
            logger.critical(f"Arquivo de template de prompt não encontrado em: {template_path}", exc_info=True)
            raise FileNotFoundError(f"Arquivo de template de prompt não encontrado. Verifique o caminho: {template_path}")
        except Exception as e:
            logger.critical(f"Erro ao carregar o template de prompt de '{template_path}': {e}", exc_info=True)
            raise RuntimeError(f"Não foi possível carregar o template de prompt: {e}")

    def _construir_prompt(self, dados_brutos: str) -> str:
        """Constrói o prompt completo usando o template carregado e os dados brutos."""
        try:
            prompt_completo = self._prompt_template_content.format(dados_brutos=dados_brutos)
            # O log sobre a versão do prompt agora é feito durante o carregamento do template.
            return prompt_completo
        except KeyError as ke:
            logger.error(f"Placeholder ausente ou incorreto no template de prompt ao formatar: {ke}. "
                         f"Certifique-se de que o template contém '{{dados_brutos}}' e nenhum outro placeholder inesperado.", exc_info=True)
            raise ValueError(f"Erro ao construir o prompt: placeholder {ke} inválido no template.")
        except Exception as e:
            logger.error(f"Erro inesperado ao construir o prompt: {e}", exc_info=True)
            raise RuntimeError(f"Erro ao construir o prompt: {e}")

    def processar_relatorio_com_ia(self, dados_brutos: str) -> str:
        if not dados_brutos or not dados_brutos.strip():
            logger.warning("Tentativa de processar relatório bruto vazio ou apenas com espaços.")
            raise ValueError("O relatório bruto não pode estar vazio.")

        prompt = self._construir_prompt(dados_brutos)
        
        logger.info(f"Enviando prompt para a API Gemini. Tamanho aprox. do prompt: {len(prompt)} caracteres.")
        try:
            response = self.model.generate_content(prompt)
            
            if response.parts:
                processed_text = response.text.strip()
                # Limpeza de possíveis blocos de markdown, embora o prompt instrua contra isso.
                if processed_text.startswith("```text"):
                    processed_text = processed_text[len("```text"):].lstrip() # lstrip para remover nova linha
                elif processed_text.startswith("```"):
                     processed_text = processed_text[len("```"):].lstrip()

                if processed_text.endswith("```"):
                    processed_text = processed_text[:-len("```")].rstrip()
                
                logger.info("Resposta recebida da API Gemini e processada com sucesso.")
                return processed_text
            else:
                block_reason_str = "Não especificado"
                safety_ratings_info_list = []

                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                        # Para Enums, .name fornece a string representativa.
                        block_reason_str = response.prompt_feedback.block_reason.name \
                            if hasattr(response.prompt_feedback.block_reason, 'name') \
                            else str(response.prompt_feedback.block_reason)
                    
                    if hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                        for rating in response.prompt_feedback.safety_ratings:
                            category_name = rating.category.name if hasattr(rating.category, 'name') else str(rating.category)
                            probability_name = rating.probability.name if hasattr(rating.probability, 'name') else str(rating.probability)
                            safety_ratings_info_list.append(f"{category_name}: {probability_name}")
                
                safety_ratings_info = ", ".join(safety_ratings_info_list) if safety_ratings_info_list else "Nenhuma classificação de segurança detalhada."
                logger.warning(f"A API Gemini não retornou conteúdo. Motivo do bloqueio: {block_reason_str}. Classificações: {safety_ratings_info}")
                
                user_error_message = f"A IA não conseguiu processar o relatório. Motivo: {block_reason_str}."
                if safety_ratings_info_list:
                    user_error_message += f" (Detalhes de segurança: {safety_ratings_info})"
                raise RuntimeError(user_error_message)

        except genai.types.BlockedPromptException as bpe:
            logger.warning(f"Prompt bloqueado pela API Gemini: {bpe}", exc_info=True)
            raise RuntimeError("Seu relatório não pôde ser processado devido a restrições de conteúdo da IA. Por favor, revise o texto.")
        except Exception as e:
            logger.error(f"Exceção inesperada ao chamar a API Gemini ou processar sua resposta: {e.__class__.__name__}: {e}", exc_info=True)
            raise RuntimeError("Ocorreu um erro de comunicação com o serviço de IA. Tente novamente mais tarde.")