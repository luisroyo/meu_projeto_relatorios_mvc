import logging
import os
import google.generativeai as genai
from flask import current_app # Embora current_app não seja usado diretamente aqui, é bom manter se planeja usar config da app

class ReportService:
    """
    Serviço responsável por interagir com a API de IA Generativa do Google
    para processar relatórios de segurança patrimonial.
    """
    def __init__(self, prompt_template_filename="patrimonial_security_report_template.txt"):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._prompt_template_content = None
        self._google_api_key = None

        try:
            self._google_api_key = os.getenv('GOOGLE_API_KEY')
            if not self._google_api_key:
                self.logger.error("API Key do Google (GOOGLE_API_KEY) não encontrada nas variáveis de ambiente.")
                raise ValueError("API Key do Google não configurada.")

            genai.configure(api_key=self._google_api_key)
            self.logger.info("Configuração da API Key do Google bem-sucedida.")

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            self.logger.info(f"ReportService: Modelo Gemini '{self.model.model_name}' inicializado com sucesso.")

        except ValueError as ve:
            self.logger.critical(f"Falha na inicialização do ReportService (configuração da API): {ve}")
            # Considerar relançar para impedir a instanciação se a API Key for vital.
        except Exception as e:
            self.logger.critical(f"Falha catastrófica na inicialização do ReportService: {e}", exc_info=True)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "prompt_templates", prompt_template_filename)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self._prompt_template_content = f.read()
            self.logger.info(f"Template de prompt '{prompt_template_filename}' carregado com sucesso de '{template_path}'.")
            # Log para ver o conteúdo exato do template lido
            self.logger.debug(f"Conteúdo do template lido para depuração:\n>>>\n{self._prompt_template_content}\n<<<")
        except FileNotFoundError:
            self.logger.error(f"Arquivo de template de prompt não encontrado: {template_path}")
            self._prompt_template_content = None
        except Exception as e:
            self.logger.error(f"Erro ao carregar o template de prompt '{template_path}': {e}", exc_info=True)
            self._prompt_template_content = None


    def _construir_prompt(self, dados_brutos: str) -> str:
        if not self._prompt_template_content:
            self.logger.error("Template de prompt não carregado ou vazio ao tentar construir o prompt.")
            raise ValueError("Template de prompt não está disponível para construir o prompt.")
        
        self.logger.debug(f"Construindo prompt. Chave esperada no template via .format(): {{dados_brutos}}. Valor para dados_brutos (tipo {type(dados_brutos)}): '{dados_brutos[:100]}...' (primeiros 100 chars)")

        try:
            # A chamada .format() espera que o template contenha {dados_brutos}
            prompt_completo = self._prompt_template_content.format(dados_brutos=dados_brutos)
            return prompt_completo
        except KeyError as e:
            # Se este erro ocorrer, 'e' será a chave que .format() não encontrou nos argumentos
            # OU uma chave que estava no template mas não foi fornecida como argumento.
            # No seu caso, o erro é KeyError: 'dados\\_brutos', o que significa que o template
            # DEVE conter um placeholder que o Python interpreta como {dados\\_brutos}
            # (ou seja, o arquivo .txt provavelmente tem literalmente dados\\_brutos dentro das chaves).
            self.logger.error(
                f"KeyError ao formatar o prompt: A chave '{e}' não foi encontrada nos argumentos fornecidos OU "
                f"o placeholder correspondente a '{e}' no template está malformado ou ausente. "
                f"Verifique se o template contém EXATAMENTE '{{dados_brutos}}' e não algo como '{{dados\\_brutos}}'."
            )
            raise ValueError(f"Erro ao construir o prompt: placeholder para a chave '{e}' está inválido ou ausente no template.")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao formatar o prompt: {e}", exc_info=True)
            raise ValueError(f"Erro inesperado ao formatar o prompt: {str(e)}")


    def processar_relatorio_com_ia(self, relatorio_bruto: str) -> str:
        if self.model is None:
            self.logger.error("Modelo de IA não inicializado. Não é possível processar.")
            raise RuntimeError("Serviço de IA não está configurado corretamente.")
        if not self._prompt_template_content:
            self.logger.error("Template de prompt não carregado. Não é possível processar.")
            raise RuntimeError("Template de prompt não está configurado corretamente.")

        if not isinstance(relatorio_bruto, str):
            self.logger.warning("Entrada 'relatorio_bruto' não é uma string.")
            raise ValueError("'relatorio_bruto' deve ser uma string.")
        if not relatorio_bruto.strip():
            self.logger.warning("Entrada 'relatorio_bruto' está vazia.")
            raise ValueError("'relatorio_bruto' não pode estar vazio.")

        try:
            prompt_final = self._construir_prompt(relatorio_bruto)
            self.logger.info(f"Enviando prompt para o modelo Gemini (primeiros 100 chars): {prompt_final[:100]}...")
            
            response = self.model.generate_content(prompt_final)
            
            self.logger.debug(f"Resposta bruta da API Gemini: {response}")
            self.logger.debug(f"Tipo da resposta da API: {type(response)}")
            if hasattr(response, 'text'):
                 self.logger.debug(f"Atributo 'text' da resposta: {response.text[:500] if response.text else 'None'}...")
            if hasattr(response, 'parts'):
                 self.logger.debug(f"Atributo 'parts' da resposta: {response.parts}")
            if hasattr(response, 'prompt_feedback'):
                 self.logger.debug(f"Atributo 'prompt_feedback' da resposta: {response.prompt_feedback}")

            if hasattr(response, 'text') and response.text:
                self.logger.info("Relatório processado pela IA com sucesso (usando response.text).")
                return response.text
            elif response.parts:
                texto_processado = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                if not texto_processado and response.prompt_feedback and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED":
                    block_reason_detail = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
                    self.logger.warning(f"Conteúdo bloqueado pela IA. Motivo: {block_reason_detail}")
                    raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
                elif not texto_processado:
                    self.logger.warning("Resposta da IA não contém texto processado ou partes válidas (após processar 'parts').")
                    if isinstance(response, str) and response.strip().lower().startswith("<!doctype html"): # Improvável para esta API
                        self.logger.error("A API Gemini retornou uma página HTML em vez de uma resposta de conteúdo válida.")
                        raise RuntimeError("Falha na comunicação com a API Gemini: resposta inesperada em formato HTML.")
                    raise ValueError("Resposta da IA está vazia ou inválida (após processar 'parts').")
                
                self.logger.info("Relatório processado pela IA com sucesso (usando response.parts).")
                return texto_processado
            elif response.prompt_feedback and str(response.prompt_feedback.block_reason) != "BLOCK_REASON_UNSPECIFIED":
                 block_reason_detail = response.prompt_feedback.block_reason_message or str(response.prompt_feedback.block_reason)
                 self.logger.warning(f"Conteúdo bloqueado pela IA (sem partes, mas com feedback). Motivo: {block_reason_detail}")
                 raise ValueError(f"O conteúdo gerado foi bloqueado pela IA. Motivo: {block_reason_detail}")
            else:
                self.logger.warning("Resposta da IA não contém 'text', 'parts' válidas ou feedback de bloqueio claro.")
                raise ValueError("Resposta da API Gemini está em formato inesperado ou vazia.")

        except ValueError as ve: 
            self.logger.error(f"Erro de valor durante o processamento com IA: {ve}")
            raise 
        except genai.types.BlockedPromptException as bpe:
            self.logger.warning(f"Prompt bloqueado pela API Gemini: {bpe}")
            raise ValueError(f"Seu prompt foi bloqueado por razões de segurança: {bpe}")
        except genai.types.StopCandidateException as sce:
            self.logger.warning(f"Geração interrompida pela API Gemini: {sce}")
            raise ValueError(f"A geração de conteúdo foi interrompida: {sce}")
        except Exception as e:
            self.logger.error(f"Erro inesperado durante a comunicação com a API Gemini: {e}", exc_info=True)
            if isinstance(getattr(e, 'response', None), str) and e.response.strip().lower().startswith("<!doctype html"):
                 self.logger.error("A exceção da API Gemini continha uma resposta HTML.")
                 raise RuntimeError("Falha na comunicação com a API Gemini: resposta inesperada em formato HTML na exceção.")
            raise RuntimeError(f"Erro de comunicação com o serviço de IA: {str(e)}")

