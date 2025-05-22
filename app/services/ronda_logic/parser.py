import logging
from datetime import datetime
from . import config # Importa config.py do mesmo diretório (ronda_logic)
from .utils import normalizar_hora_capturada # Importa de utils.py do mesmo diretório

logger = logging.getLogger(__name__)

def parse_linha_log(linha_strip: str, ultima_data_valida: str, ultima_vtr: str, data_plantao_manual: str):
    data_log_linha = None
    id_vtr_linha = None
    mensagem_eventos = None
    
    match_prefixo = config.REGEX_PREFIXO_LINHA.match(linha_strip) # Usa config.
    if match_prefixo:
        data_log_linha = match_prefixo.group(1)
        vtr_match = match_prefixo.group(2)
        mensagem_eventos = match_prefixo.group(3).strip()
        
        if vtr_match:
            id_vtr_linha = vtr_match.upper().replace(" ", "")
            ultima_vtr = id_vtr_linha
        else:
            match_vtr_msg = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(mensagem_eventos) # Usa config.
            if match_vtr_msg:
                id_vtr_linha = match_vtr_msg.group(1).upper().replace(" ", "")
                mensagem_eventos = match_vtr_msg.group(2).strip()
                ultima_vtr = id_vtr_linha
            else:
                id_vtr_linha = ultima_vtr
        ultima_data_valida = data_log_linha
    else:
        data_log_linha = ultima_data_valida or data_plantao_manual
        if not data_log_linha:
            return None, None, None, ultima_data_valida, ultima_vtr

        match_vtr_msg_alt = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(linha_strip) # Usa config.
        if match_vtr_msg_alt:
            id_vtr_linha = match_vtr_msg_alt.group(1).upper().replace(" ", "")
            mensagem_eventos = match_vtr_msg_alt.group(2).strip()
            ultima_vtr = id_vtr_linha
        else:
            mensagem_eventos = linha_strip
            id_vtr_linha = ultima_vtr
            
    return data_log_linha, id_vtr_linha, mensagem_eventos, ultima_data_valida, ultima_vtr

def extrair_detalhes_evento(mensagem: str, data_log: str, id_vtr: str, linha_original_str: str, vtr_fallback: str):
    if not mensagem:
        return None

    for r_info in config.COMPILED_RONDA_EVENT_REGEXES: # Usa config.
        match_evento = r_info["regex"].search(mensagem)
        if match_evento:
            hora_evento_raw = match_evento.group(1)
            hora_formatada = normalizar_hora_capturada(hora_evento_raw) # Usa de .utils
            
            if hora_formatada and data_log:
                dt_evento_str = f"{data_log} {hora_formatada}"
                try:
                    dt_obj = datetime.strptime(dt_evento_str, "%d/%m/%Y %H:%M")
                    return {
                        "vtr": id_vtr or vtr_fallback,
                        "tipo": r_info["tipo"],
                        "hora_str": hora_formatada,
                        "data_str": data_log,
                        "datetime_obj": dt_obj,
                        "linha_original": linha_original_str
                    }
                except ValueError as ve:
                    logger.error(f"  Erro de data/hora ao parsear evento '{linha_original_str}': {ve}. Data str: '{data_log}', Hora formatada: '{hora_formatada}'")
                    return None
    return None