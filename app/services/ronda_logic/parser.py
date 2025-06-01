# parser.py
import logging
from datetime import datetime
from . import config # Importa config.py do mesmo diretório (ronda_logic)
from .utils import normalizar_hora_capturada # Importa de utils.py do mesmo diretório

logger = logging.getLogger(__name__)

def parse_linha_log(linha_strip: str,
                    _param_ultima_data_valida_ignorada: str, 
                    ultima_vtr: str,
                    data_fixa_para_eventos: str):
    
    data_log_atribuida = data_fixa_para_eventos
    id_vtr_linha = None
    mensagem_eventos = None
    data_original_na_linha = None 

    match_prefixo = config.REGEX_PREFIXO_LINHA.match(linha_strip)
    if match_prefixo:
        data_original_na_linha = match_prefixo.group(1)
        vtr_match = match_prefixo.group(2)
        mensagem_eventos = match_prefixo.group(3).strip()
        
        if data_original_na_linha and data_fixa_para_eventos != config.FALLBACK_DATA_INDEFINIDA and data_original_na_linha != data_fixa_para_eventos:
            logger.info(f"  Data original da linha '{data_original_na_linha}' difere da data do plantão '{data_fixa_para_eventos}'. Usando data do plantão. Linha: '{linha_strip[:100]}...'")

        if vtr_match:
            id_vtr_linha = vtr_match.upper().replace(" ", "")
            ultima_vtr = id_vtr_linha
        else: 
            match_vtr_msg = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(mensagem_eventos)
            if match_vtr_msg:
                id_vtr_linha = match_vtr_msg.group(1).upper().replace(" ", "")
                mensagem_eventos = match_vtr_msg.group(2).strip()
                ultima_vtr = id_vtr_linha
            else: 
                id_vtr_linha = ultima_vtr
    else: 
        match_vtr_msg_alt = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(linha_strip)
        if match_vtr_msg_alt:
            id_vtr_linha = match_vtr_msg_alt.group(1).upper().replace(" ", "")
            mensagem_eventos = match_vtr_msg_alt.group(2).strip()
            ultima_vtr = id_vtr_linha
        else: 
            mensagem_eventos = linha_strip
            id_vtr_linha = ultima_vtr
            
    quarto_valor_retorno = data_original_na_linha if data_original_na_linha else _param_ultima_data_valida_ignorada
    return data_log_atribuida, id_vtr_linha, mensagem_eventos, quarto_valor_retorno, ultima_vtr


def extrair_detalhes_evento(mensagem: str, data_log: str, id_vtr: str, linha_original_str: str, vtr_fallback: str):
    if not mensagem:
        return None

    for r_info in config.COMPILED_RONDA_EVENT_REGEXES:
        match_evento = r_info["regex"].search(mensagem)
        if match_evento:
            # Tenta obter o grupo de captura da hora. Algumas regex podem não ter (embora todos os atuais tenham).
            hora_evento_raw = None
            try:
                hora_evento_raw = match_evento.group(1) # Assumindo que a hora é sempre o primeiro grupo de captura
            except IndexError:
                logger.error(f"  Regex '{r_info['regex'].pattern}' encontrou um match em '{mensagem}' mas não possui grupo de captura para hora.")
                continue # Tenta a próxima regex

            if hora_evento_raw is None: # Se o grupo existe mas não capturou (improvável com os padrões atuais)
                logger.warning(f"  Regex '{r_info['regex'].pattern}' encontrou um match em '{mensagem}' mas o grupo da hora é None.")
                continue

            hora_formatada = normalizar_hora_capturada(hora_evento_raw)
            
            if not hora_formatada: # Se a normalização falhar e retornar string vazia
                logger.warning(f"  Hora não pôde ser normalizada a partir de '{hora_evento_raw}' na linha '{linha_original_str}'. Evento ignorado.")
                return None # Ou poderia tentar com a hora_evento_raw, mas arrisca erro no strptime

            if data_log:
                if data_log == config.FALLBACK_DATA_INDEFINIDA:
                    logger.error(f"  Não é possível criar data/hora para evento '{linha_original_str}' porque a data do plantão é indefinida ('{data_log}').")
                    # Não retorna None aqui ainda, pode haver outra regex que funcione melhor,
                    # mas se esta for a única, e a data for indefinida, o strptime falhará.
                    # No entanto, como a data é fixada para todos os eventos, se for indefinida, todos falharão.
                    # Melhor retornar None aqui para evitar tentativas repetidas de erro no strptime.
                    return None 

                dt_evento_str = f"{data_log} {hora_formatada}"
                try:
                    dt_obj = datetime.strptime(dt_evento_str, "%d/%m/%Y %H:%M")
                    return {
                        "vtr": id_vtr or vtr_fallback or config.DEFAULT_VTR_ID, # Garante que VTR nunca seja None
                        "tipo": r_info["tipo"],
                        "hora_str": hora_formatada,
                        "data_str": data_log,
                        "datetime_obj": dt_obj,
                        "linha_original": linha_original_str
                    }
                except ValueError as ve:
                    logger.error(f"  Erro de data/hora ao parsear evento '{linha_original_str}': {ve}. Data str fornecida: '{data_log}', Hora formatada: '{hora_formatada}' (Raw: '{hora_evento_raw}')")
                    # Não retorna None imediatamente, pois outra regex pode capturar a hora de forma diferente
                    # e resultar em sucesso. Se todas falharem, esta função retornará None no final.
                    # No entanto, se a data_log ou hora_formatada são o problema, vai falhar para todas.
                    # Considerar retornar None se a falha for claramente devido a data_log inválida.
                    # Se data_log passou pela validação no processor.py, então o problema é mais provável na hora_formatada.
                    # Se a hora_formatada é o resultado de normalizar_hora_capturada, e esta retorna a original em caso de erro,
                    # é aqui que o strptime vai falhar.
                    return None # Retornar None aqui é mais seguro se o strptime falhou.
            else: # data_log é None ou vazia
                logger.error(f"  Data do log ausente para o evento na linha '{linha_original_str}'.")
                return None
    return None