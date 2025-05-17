import os
import google.generativeai as genai # Descomente esta linha ou adicione se não estiver lá

class ReportService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            # Este erro será capturado pelo __init__.py do app ou pelo routes.py
            # se o serviço não puder ser instanciado.
            raise ValueError("API Key do Google não configurada no arquivo .env. O serviço não pode operar.")

        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            # Captura erros na configuração da API key (ex: chave inválida no formato)
            raise ValueError(f"Erro ao configurar a API Key do Google: {e}")

        # Configurações do modelo Gemini
        self.generation_config = {
            "temperature": 0.7, # Controla a criatividade. Valores menores = mais determinístico.
            "top_p": 1,
            "top_k": 1, # Em alguns guias, top_k=32 ou similar pode ser usado. Para este caso, 1 é direto.
            "max_output_tokens": 4096, # Aumente se seus relatórios processados forem muito longos
        }

        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        try:
            self.model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest", # Modelo rápido e eficiente
                                              generation_config=self.generation_config,
                                              safety_settings=self.safety_settings)
            print("ReportService: Modelo Gemini inicializado com sucesso.")
        except Exception as e:
            # Captura erros na inicialização do modelo (ex: nome do modelo inválido, problemas de permissão)
            raise RuntimeError(f"Erro ao inicializar o modelo Gemini: {e}")

    def _construir_prompt(self, dados_brutos: str) -> str:
        # ESTE É O PROMPT DETALHADO QUE VOCÊ CRIOU ANTERIORMENTE.
        # Ajuste conforme o exemplo de "dado bruto" e "dado limpo" que você me passou.
        prompt_completo = f"""
        Objetivo: Transformar um relatório bruto em um relatório estruturado, corrigido e profissional.

        Instruções Detalhadas:
        1.  Analise o "Relatório Bruto" fornecido.
        2.  Extraia todas as informações relevantes.
        3.  Corrija erros gramaticais e ortográficos.
        4.  Formate a data para DD/MM/AAAA.
        5.  Apresente o resultado final estritamente no formato especificado em "Formato de Saída". Não inclua nenhuma frase ou texto fora deste formato.
        6.  Se alguma informação não estiver presente no relatório bruto, omita o campo correspondente ou deixe-o em branco no formato de saída, a menos que possa ser inferida com alta certeza (ex: "Acionamentos: (x) Central" se o texto disser "central acionou").
        7.  Para a seção "Relato", crie uma narrativa coesa e formal, em terceira pessoa, descrevendo os eventos. Integre informações como agente, viatura, e a relação entre empresas (ex: NorteSul como contratada da Sanasa) de forma fluida.
        8.  Na seção "Acionamentos", marque com "(x)" apenas o que foi explicitamente mencionado ou fortemente implícito. Deixe os outros com "( )".

        Formato de Saída Esperado:
        ```text
        Data: [DD/MM/AAAA]
        Hora: [HH:MM]
        Local: [Endereço completo e detalhado, com correções se necessário, ex: "Avenida" em vez de "Av"]
        Ocorrência: [Título curto e formal da ocorrência, ex: "Verificação de caminhão parado"]

        Relato:
        [Narrativa detalhada e formal dos fatos, incluindo nomes, agente, viatura, e o que foi constatado.
        Exemplo: "A central de monitoramento acionou a VTR [Número da VTR], conduzida pelo agente [Nome do Agente], para averiguar um caminhão estacionado em [Local Referência]. Ao chegar ao local, foi feito contato com o condutor, identificado como [Nome do Condutor]. Ele informou que, juntamente com [Outros Envolvidos, se houver], presta serviços à empresa [Nome da Empresa Prestadora], responsável por manutenções na rede de esgoto contratadas pela [Nome da Empresa Contratante, se houver]."]

        Ações Realizadas:
        - Verificação da situação e contato com os envolvidos.
        (Adicione outras ações se mencionadas ou inferíveis)

        Acionamentos:
        ( ) Central
        ( ) Apoio 90
        ( ) Polícia Militar
        ( ) Supervisor
        ( ) Coordenador

        Envolvidos/Testemunhas:
        - [Nome do Envolvido 1] ([Função/Detalhe, ex: motorista]) – [Empresa, se aplicável]
        - [Nome do Envolvido 2] ([Função/Detalhe]) – [Empresa, se aplicável]

        Veículo:
        [Tipo do Veículo] [Marca], placa [Placa]

        Responsável pelo registro:
        [Nome do Agente]
        ```

        Relatório Bruto para processar:
        ---
        {dados_brutos}
        ---

        Relatório Processado:
        """
        # print(f"DEBUG: Prompt construído:\n{prompt_completo[:500]}...") # Para debug, se necessário
        return prompt_completo

    def processar_relatorio_com_ia(self, dados_brutos: str) -> str:
        if not dados_brutos or not dados_brutos.strip():
            raise ValueError("O relatório bruto não pode estar vazio.")

        prompt = self._construir_prompt(dados_brutos)

        print(f"INFO: Enviando prompt para a API Gemini. Tamanho do prompt: {len(prompt)} caracteres.")
        try:
            # Geração de conteúdo usando o modelo
            response = self.model.generate_content(prompt)

            # Verifica se há texto na resposta e se não foi bloqueado
            if response.parts:
                # Remove os ```text e ``` do início e fim, se presentes, para limpar a saída
                processed_text = response.text.strip()
                if processed_text.startswith("```text"):
                    processed_text = processed_text[len("```text"):].strip()
                if processed_text.endswith("```"):
                    processed_text = processed_text[:-len("```")].strip()

                print("INFO: Resposta recebida da API Gemini e processada.")
                return processed_text
            else:
                # Isso pode acontecer se a resposta foi bloqueada ou não houve candidato.
                # Verifique response.prompt_feedback para detalhes do bloqueio.
                block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Não especificado"
                print(f"AVISO: A API Gemini não retornou conteúdo. Motivo do bloqueio: {block_reason}")
                # Tenta obter informações de segurança se houver
                safety_ratings_info = ""
                if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                    safety_ratings_info = ", ".join([f"{rating.category.name}: {rating.probability.name}" for rating in response.prompt_feedback.safety_ratings])

                error_message = f"A IA não conseguiu processar o relatório. Motivo: {block_reason}."
                if safety_ratings_info:
                    error_message += f" Classificações de segurança: {safety_ratings_info}"

                # Lança um erro que será capturado pelo controller e mostrado ao usuário
                raise RuntimeError(error_message)

        except Exception as e:
            # Captura outras exceções da API ou do processamento da resposta
            print(f"ERRO: Exceção ao chamar a API Gemini ou processar sua resposta: {e.__class__.__name__}: {e}")
            # Re-levanta um erro genérico ou mais específico para o controller tratar
            raise RuntimeError(f"Ocorreu um erro ao comunicar com o serviço de IA: {e}")