import os
import google.generativeai as genai
import logging

# Logger específico para este módulo
# Ele herdará a configuração básica definida em app/__init__.py
logger = logging.getLogger(__name__)

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
            "temperature": 0.6, # Ajustado para um pouco menos de criatividade, mais factual
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 4096,
        }

        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        try:
            self.model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest",
                                              generation_config=self.generation_config,
                                              safety_settings=self.safety_settings)
            logger.info("ReportService: Modelo Gemini inicializado com sucesso.")
        except Exception as e:
            logger.critical(f"Erro crítico ao inicializar o modelo Gemini: {e}", exc_info=True)
            raise RuntimeError(f"Erro ao inicializar o modelo Gemini: {e}")

    def _construir_prompt(self, dados_brutos: str) -> str:
        # ESTE É O PROMPT DETALHADO QUE VOCÊ CRIOU ANTERIORMENTE.
        # Revise e ajuste conforme necessário para otimizar os resultados da IA.
        prompt_completo = f"""
        Objetivo: Transformar um relatório bruto em um relatório estruturado, corrigido e profissional.

        Instruções Detalhadas:
        1.  Analise o "Relatório Bruto" fornecido.
        2.  Extraia todas as informações relevantes.
        3.  Corrija erros gramaticais e ortográficos.
        4.  Formate a data para DD/MM/AAAA. Se o ano for fornecido com dois dígitos (ex: 25), interprete-o como 2025.
        5.  Apresente o resultado final estritamente no formato especificado em "Formato de Saída". Não inclua nenhuma frase ou texto introdutório ou conclusivo fora deste formato. Não use markdown de bloco de código (```text ... ```) na saída final.
        6.  Se alguma informação não estiver presente no relatório bruto, omita o campo correspondente ou deixe o valor do campo em branco no formato de saída, a menos que possa ser inferida com alta certeza (ex: "Acionamentos: (x) Central" se o texto disser "central acionou").
        7.  Para a seção "Relato", crie uma narrativa coesa e formal, em terceira pessoa, descrevendo os eventos. Integre informações como agente, viatura, e a relação entre empresas (ex: NorteSul como contratada da Sanasa) de forma fluida.
        8.  Na seção "Acionamentos", marque com "(x)" apenas o que foi explicitamente mencionado ou fortemente implícito. Deixe os outros com "( )". Se nada for mencionado sobre acionamentos específicos, deixe todos como "( )".

        Formato de Saída Esperado:
        Data: [DD/MM/AAAA]
        Hora: [HH:MM]
        Local: [Endereço completo e detalhado, com correções se necessário, ex: "Avenida" em vez de "Av"]
        Ocorrência: [Título curto e formal da ocorrência, ex: "Verificação de caminhão parado"]

        Relato:
        [Narrativa detalhada e formal dos fatos, incluindo nomes, agente, viatura, e o que foi constatado.
        Exemplo: "A central de monitoramento acionou a VTR [Número da VTR], conduzida pelo agente [Nome do Agente], para averiguar um caminhão estacionado em [Local Referência]. Ao chegar ao local, foi feito contato com o condutor, identificado como [Nome do Condutor]. Ele informou que, juntamente com [Outros Envolvidos, se houver], presta serviços à empresa [Nome da Empresa Prestadora], responsável por manutenções na rede de esgoto contratadas pela [Nome da Empresa Contratante, se houver]."]

        Ações Realizadas:
        - Verificação da situação e contato com os envolvidos.
        (Adicione outras ações se mencionadas ou inferíveis, cada uma em uma nova linha iniciada por "- ")

        Acionamentos:
        ( ) Central ( ) Apoio 90 ( ) Polícia Militar ( ) Supervisor ( ) Coordenador

        Envolvidos/Testemunhas:
        - [Nome do Envolvido 1] ([Função/Detalhe, ex: motorista]) – [Empresa, se aplicável]
        - [Nome do Envolvido 2] ([Função/Detalhe]) – [Empresa, se aplicável]
        (Liste cada envolvido em uma nova linha iniciada por "- ")

        Veículo:
        [Tipo do Veículo] [Marca], placa [Placa]

        Responsável pelo registro:
        [Nome do Agente]

        Relatório Bruto para processar:
        ---
        {dados_brutos}
        ---

        Relatório Processado:
        """
        # logger.debug(f"Prompt construído:\n{prompt_completo[:500]}...") # Use DEBUG para prompts longos
        return prompt_completo

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
                # A instrução no prompt para não usar ```text deveria ser suficiente,
                # mas uma verificação dupla não faz mal.
                if processed_text.startswith("```text"):
                    processed_text = processed_text[len("```text"):].strip()
                if processed_text.endswith("```"):
                    processed_text = processed_text[:-len("```")].strip()
                
                logger.info("Resposta recebida da API Gemini e processada com sucesso.")
                return processed_text
            else:
                block_reason = "Não especificado"
                safety_ratings_info_list = []
                if response.prompt_feedback:
                    block_reason = response.prompt_feedback.block_reason if response.prompt_feedback.block_reason else block_reason
                    if response.prompt_feedback.safety_ratings:
                        for rating in response.prompt_feedback.safety_ratings:
                            safety_ratings_info_list.append(f"{rating.category.name}: {rating.probability.name}")
                
                safety_ratings_info = ", ".join(safety_ratings_info_list) if safety_ratings_info_list else "Nenhuma classificação de segurança detalhada."
                logger.warning(f"A API Gemini não retornou conteúdo. Motivo do bloqueio: {block_reason}. Classificações: {safety_ratings_info}")
                
                user_error_message = f"A IA não conseguiu processar o relatório. Motivo: {block_reason}."
                if safety_ratings_info_list: # Adiciona detalhes se existirem
                    user_error_message += f" (Detalhes de segurança: {safety_ratings_info})"
                raise RuntimeError(user_error_message)

        except genai.types.BlockedPromptException as bpe:
            logger.warning(f"Prompt bloqueado pela API Gemini: {bpe}", exc_info=True)
            raise RuntimeError(f"Seu relatório não pôde ser processado devido a restrições de conteúdo da IA. Por favor, revise o texto.")
        except Exception as e:
            logger.error(f"Exceção inesperada ao chamar a API Gemini ou processar sua resposta: {e.__class__.__name__}: {e}", exc_info=True)
            raise RuntimeError(f"Ocorreu um erro de comunicação com o serviço de IA. Tente novamente mais tarde.")