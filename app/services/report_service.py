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

    # Dentro da classe ReportService em app/services/report_service.py

    # Dentro da classe ReportService em app/services/report_service.py

    # Dentro da classe ReportService em app/services/report_service.py

    # Dentro da classe ReportService em app/services/report_service.py

    # Dentro da classe ReportService em app/services/report_service.py

    def _construir_prompt(self, dados_brutos: str) -> str:
        # Logger já deve estar definido no __init__ do serviço ou no topo do arquivo
        # logger.debug(f"Construindo prompt para dados brutos: {dados_brutos[:100]}...")

        prompt_completo = f"""
        **Tarefa Principal:**
        Você é um assistente de IA altamente competente, especializado em processar e reestruturar relatórios de ocorrências de segurança patrimonial. Sua função é transformar o "Relatório Bruto" fornecido, que muitas vezes pode conter erros de português e não ter uma estrutura definida, em um "Relatório Processado" formal, claro, conciso, gramaticalmente correto e bem organizado.

        **Contexto Operacional (Muito Importante):**
        Os relatórios são gerados para um grande complexo que inclui múltiplas áreas comuns externas e 18 residenciais/condomínios internos.
        As ocorrências são geralmente identificadas pela "Central de Monitoramento" através de câmeras de segurança.
        A Central de Monitoramento aciona as equipes de "VTR" (Veículo Tático de Rondas) para averiguações e ações.
        Quando uma situação aparenta risco excessivo que demande uma equipe armada interna, a "Apoio 90" pode ser acionada. A "Apoio 90" NÃO é a Polícia Militar; é uma equipe de suporte armado interno do próprio complexo.
        O relatório bruto é o registro feito pela equipe da VTR, pelo operador da central ou pela equipe do Apoio 90.

        **Instruções Detalhadas para Processamento:**

        1.  **Análise e Extração:** Leia atentamente o "Relatório Bruto" para extrair todas as informações pertinentes.
        2.  **Correção de Português:** Corrija TODOS os erros de gramática, ortografia, pontuação e concordância.
        3.  **Melhoria da Redação:** Reescreva frases de forma clara, objetiva e profissional. Se o texto bruto for muito telegráfico ou informal, elabore-o para garantir clareza e um tom formal, mas SEM inventar informações que não estejam implícitas no texto original. O objetivo é melhorar a apresentação dos fatos, não alterá-los.
        4.  **Interpretação de "Pernoite de Veículo" (REGRA IMPORTANTE):** Se o relatório bruto indicar que um veículo está com problemas e, como consequência, "irá pernoitar no complexo" (ou expressão similar), interprete que é o **VEÍCULO** que permanecerá no local, e não necessariamente a pessoa (condutor/proprietário), a menos que o texto afirme explicitamente que a PESSOA irá pernoitar. No "Relato" e/ou "Ações Realizadas", deixe claro que o veículo ficará no local. Exemplo: "O veículo Ford Fiesta permanecerá no local para reparo/remoção posterior."
        5.  **Adaptabilidade:** O relatório bruto pode ser desestruturado. Sua tarefa é identificar as informações e encaixá-las nos campos corretos do "Formato de Saída Esperado".
        6.  **Formato de Data e Hora:** Padronize a data para DD/MM/AAAA (se o ano for fornecido com dois dígitos, como "25", interprete-o como "2025") e a hora para HH:MM.
        7.  **Nomenclatura de VTRs (REGRA IMPORTANTE):** Se o relatório bruto mencionar uma VTR seguida de um número (ex: "VTR 03", "vtr 10", "Viatura 03", "vtr03", "AGUIA 07"), na saída formatada, SEMPRE substitua "VTR", "Viatura" ou "AGUIA" (e variações de caixa) por "Águia-" seguido do número formatado com dois dígitos se for menor que 10 (ex: "VTR 3" ou "vtr03" ou "AGUIA 07" se torna "Águia-07", "vtr 10" se torna "Águia-10"). Aplique esta substituição em todos os campos do relatório processado onde a VTR for mencionada.
        8.  **Artigo para "Águia-XX" (REGRA DE ESTILO IMPORTANTE):** Ao se referir textualmente às unidades "Águia-XX" (ex: Águia-03, Águia-10), sempre utilize o artigo masculino ("o", "os", "um", "uns"). Por exemplo, escreva "o Águia-03 chegou ao local" ou "um chamado para o Águia-10", e NUNCA "a Águia-03" ou "uma Águia-10". Trate a designação "Águia-XX" como uma referência a uma entidade masculina no contexto operacional (como "o veículo" ou "o time").
        9.  **Estrutura de Saída:** Siga RIGOROSAMENTE o "Formato de Saída Esperado" abaixo. Não adicione seções não solicitadas nem omita as seções pedidas (se houver informação para elas). Se uma informação específica para um campo não estiver presente no relatório bruto, deixe o valor do campo em branco. Não inclua markdown de bloco de código (```text ... ```) na saída final.

        **Instruções Específicas para Cada Campo do "Formato de Saída Esperado":**

        * **Data:** Data da ocorrência.
        * **Hora:** Hora aproximada do evento principal ou do acionamento.
        * **Local (REGRA DE ENDEREÇO IMPORTANTE):**
            1.  Se o relatório bruto contiver uma indicação explícita de endereço sob um cabeçalho como "Local:" (ex: "Local: Rua X, nº 123"), use este endereço como a informação principal e transcreva-o fielmente.
            2.  Se a descrição da ocorrência mencionar um ponto de referência ou local mais específico onde o evento ocorreu (ex: "no estacionamento do mercado Y", "portaria do condomínio Z", "fundos do bloco C"), essa informação deve ser usada para complementar o endereço principal, se este existir, ou como o local principal se nenhum outro endereço for fornecido. Exemplo de combinação: "Rua X, nº 123, no estacionamento do mercado Y".
            3.  **NÃO** altere um endereço principal explicitamente fornecido para "próximo a..." apenas porque um ponto de referência foi mencionado na descrição. Se o relatório diz "Local: Rua X, 123" e a descrição diz "verificação no mercado em frente", o Local deve ser "Rua X, nº 123 (em frente ao mercado)". Mantenha a fidelidade ao endereço principal reportado como o local da averiguação ou do evento principal.
            4.  Se o guarda esquecer de mencionar "Avenida", "Rua", etc., adicione se for óbvio pelo contexto (ex: "AV.FRANCISCO ALFREDO JUNIOR" vira "Avenida Francisco Alfredo Junior"), mas priorize a transcrição fiel do nome e número fornecidos.
        * **Ocorrência:** Um título curto e objetivo que resuma o motivo do acionamento ou o principal evento.
        * **Relato:** Descrição detalhada, formal e cronológica. Inclua como a equipe foi acionada, o que foi encontrado, contatos, informações coletadas, e o desfecho (incluindo se o VEÍCULO pernoitará, conforme regra de interpretação).
        * **Ações Realizadas:** Liste em tópicos as principais ações tomadas.
        * **Acionamentos:**
            * `( ) Central`: **REGRA IMPORTANTE:** Marque com (x) se a Central de Monitoramento recebeu a informação inicial, despachou uma equipe (VTR/Águia, Apoio 90), ou se comunicou com a equipe durante a ocorrência. Se o relato indicar que a "Central de Monitoramento foi contatada" ou "acionou a equipe", este item DEVE ser marcado com (x).
            * `( ) Apoio 90 `: Marque com (x) se a equipe Apoio 90 foi acionada ou envolvida.
            * `( ) Polícia Militar (190)`: Marque com (x) se a PM foi acionada. Detalhes se houver.
            * `( ) Supervisor`: Marque com (x) se um supervisor foi contatado. Nome se mencionado.
            * `( ) Coordenador`: Marque com (x) se um coordenador foi contatado.
            * `( ) Outro`: [especificar]
        * **Envolvidos/Testemunhas:** Liste pessoas relevantes.
        * **Veículo (envolvido na ocorrência):** Detalhes de veículos CIVIS. Se a ocorrência for sobre um veículo com problemas, liste-o aqui.
        * **Responsável pelo registro (REGRA DE FORMATAÇÃO IMPORTANTE):**
            1.  Procure por um nome de guarda individual, geralmente associado a "Ronda:", "Guarda:", "Agente:" (ex: "Agente: KAUÃ").
            2.  Se um nome de guarda individual for encontrado, o formato deve ser "Guarda Patrimonial [Nome do Guarda]" (ex: "Guarda Patrimonial Kauã").
            3.  Se apenas a designação da VTR/Águia for clara e nenhum nome individual (ex: "Seguranças: AGUIA 07" e não houver campo "Agente:"), use "Equipe Águia-XX" (ex: "Equipe Águia-07").
            4.  Dê prioridade ao nome do guarda individual se disponível.

        **Formato de Saída Esperado:**
        Data: [DD/MM/AAAA]
        Hora: [HH:MM]
        Local: [Descrição detalhada conforme instruções, priorizando endereço explícito]
        Ocorrência: [Título objetivo conforme instruções]

        Relato:
        [Narrativa detalhada, formal e cronológica, conforme instruções, usando a nomenclatura e artigos corretos como "o Águia-XX" para VTRs, e esclarecendo se o VEÍCULO pernoitará]

        Ações Realizadas:
        - [Ação 1]
        - [Ação 2]
        - ...

        Acionamentos:
        ( ) Central
        ( ) Apoio 90
        ( ) Polícia Militar (190) - Detalhes: [se houver]
        ( ) Supervisor - Nome: [se houver]
        ( ) Coordenador
        ( ) Outro: [especificar, se houver]

        Envolvidos/Testemunhas:
        - [Nome/Identificação], [Função/Observação]
        - ...

        Veículo (envolvido na ocorrência):
        [Tipo] [Marca], placa [Placa], cor [Cor], [Outros detalhes relevantes]

        Responsável pelo registro:
        [Formato: "Guarda Patrimonial [Nome]" ou "Equipe Águia-XX", conforme instruções]
       

        Relatório Bruto para processar:
        ---
        {dados_brutos}
      

        Relatório Processado:
        """
        logger.info("Prompt (versão guarda patrimonial v5 - pernoite veículo, acionamento central) construído com sucesso.")
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