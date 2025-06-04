# utils.py
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def normalizar_hora_capturada(hora_str_raw: str) -> str:
    """Normaliza uma string de hora capturada para HH:MM."""
    if hora_str_raw is None:
        logger.warning("Tentativa de normalizar hora_str_raw que é None.")
        return "" 

    hora_str_trabalho = str(hora_str_raw).strip() 
    hora_lower_para_h = hora_str_trabalho.lower() 

    if hora_lower_para_h.endswith("hs"):
        hora_str_trabalho = hora_str_trabalho[:-2].strip()
        hora_lower_para_h = hora_lower_para_h[:-2].strip()
    elif hora_lower_para_h.endswith("hrs"):
        hora_str_trabalho = hora_str_trabalho[:-3].strip()
        hora_lower_para_h = hora_lower_para_h[:-3].strip()

    # Padrão para HHhMM (ex: 06h30, 18H00) ou HHh (ex: 6h, 18H) ou HH;MM
    # A regex nos eventos agora pode capturar HH;MM diretamente como grupo(1)
    # Esta função precisa lidar com o que foi capturado.

    # Prioridade para formatos com 'h' como separador ou sufixo
    match_h_format = re.fullmatch(r"(\d{1,2})h(\d{2})?", hora_lower_para_h) # 06h30, 6h
    if match_h_format:
        h_str = match_h_format.group(1)
        m_str = match_h_format.group(2) if match_h_format.group(2) else "00" 
        try:
            h, m = int(h_str), int(m_str)
            if 0 <= h <= 23 and 0 <= m <= 59: return f"{h:02d}:{m:02d}"
            else: logger.warning(f"Valores de hora/minuto fora do intervalo em formato 'h': '{hora_str_raw}' -> H:{h}, M:{m}"); return hora_str_raw 
        except ValueError: logger.warning(f"Formato 'h' inválido (não numérico) após match: '{hora_str_raw}'"); return hora_str_raw

    # Remove todos os espaços internos para formatos como "18 : 48" -> "18:48"
    # Isso também afetaria "03 ; 19" -> "03;19"
    hora_str_limpa = "".join(hora_str_trabalho.split())

    # Formatos HH:MM ou HH;MM (após limpezas e transformações)
    parts = []
    separador_encontrado = None
    if ':' in hora_str_limpa:
        parts = hora_str_limpa.split(':')
        separador_encontrado = ':'
    elif ';' in hora_str_limpa: # <--- ADICIONADO SUPORTE PARA PONTO E VÍRGULA
        parts = hora_str_limpa.split(';')
        separador_encontrado = ';'
    
    if len(parts) == 2:
        try:
            h_val_str, m_val_str = parts[0], parts[1]
            # Checa se os minutos podem ter 'h' (ex: 06h, a regex TIME_CAPTURE pode pegar "06h")
            # No entanto, normalizar_hora_capturada é chamada com o grupo(1) da regex.
            # Se o grupo(1) for "06h", o match_h_format acima já o pegaria.
            # Se o grupo(1) for "03;19", parts será ["03", "19"].
            
            h = int(h_val_str)
            m = int(m_val_str) # Se m_val_str for "19" de "03;19", isso é ok.

            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
            else:
                logger.warning(f"Valores de hora/minuto fora do intervalo ('{separador_encontrado}'): '{hora_str_raw}' -> H:{h}, M:{m}")
                return hora_str_raw 
        except ValueError: 
            logger.warning(f"Formato de hora inválido (não numérico) após split por '{separador_encontrado}': '{hora_str_limpa}' (original: '{hora_str_raw}')")
            return hora_str_raw

    # Formatos numéricos diretos: HMM, HHMM (ex: 700 -> 07:00, 1800 -> 18:00)
    # Isso só se aplica se não houver separador e for puramente numérico.
    if separador_encontrado is None and "h" not in hora_str_limpa.lower() and hora_str_limpa.isdigit():
        if len(hora_str_limpa) == 3: # HMM
            h_str, m_str = hora_str_limpa[0], hora_str_limpa[1:]
            hora_str_limpa_fmt = f"0{h_str}:{m_str}"
        elif len(hora_str_limpa) == 4: # HHMM
            h_str, m_str = hora_str_limpa[:2], hora_str_limpa[2:]
            hora_str_limpa_fmt = f"{h_str}:{m_str}"
        elif len(hora_str_limpa) == 1: # H
             hora_str_limpa_fmt = f"0{hora_str_limpa}:00"
        elif len(hora_str_limpa) == 2: # HH
             hora_str_limpa_fmt = f"{hora_str_limpa}:00"
        else:
            logger.warning(f"Formato de hora numérico não esperado: '{hora_str_raw}' (limpo: '{hora_str_limpa}')")
            return hora_str_raw
        
        # Valida o resultado da conversão numérica
        try:
            h_temp, m_temp = map(int, hora_str_limpa_fmt.split(':'))
            if 0 <= h_temp <= 23 and 0 <= m_temp <= 59: return hora_str_limpa_fmt
            else: logger.warning(f"Hora numérica convertida inválida: {hora_str_limpa_fmt} de '{hora_str_raw}'"); return hora_str_raw
        except ValueError: logger.warning(f"Erro ao validar hora numérica convertida: {hora_str_limpa_fmt} de '{hora_str_raw}'"); return hora_str_raw
            
    logger.warning(f"Formato de hora não reconhecido para normalização: '{hora_str_raw}' (processado como: '{hora_str_trabalho}', limpo: '{hora_str_limpa}')")
    return hora_str_raw

def normalizar_data_capturada(data_str_raw: str) -> str:
    # ... (manter como na última versão) ...
    if not data_str_raw: return ""
    data_str_limpa = data_str_raw.strip(); partes = []
    if '/' in data_str_limpa: partes = data_str_limpa.split('/')
    elif '-' in data_str_limpa: partes = data_str_limpa.split('-')
    elif '.' in data_str_limpa: partes = data_str_limpa.split('.')
    else: logger.warning(f"Separador de data não reconhecido em '{data_str_raw}'"); return data_str_raw
    if len(partes) == 3:
        try:
            dia, mes, ano_str = partes[0], partes[1], partes[2]
            ano = ano_str
            if len(ano_str) == 2: ano = "20" + ano_str
            elif len(ano_str) != 4: logger.warning(f"Formato de ano inválido '{ano_str}' em '{data_str_raw}'"); return data_str_raw
            # Tenta criar um objeto datetime para validar a data completa
            datetime.strptime(f"{int(dia):02d}/{int(mes):02d}/{ano}", "%d/%m/%Y")
            return f"{int(dia):02d}/{int(mes):02d}/{ano}"
        except ValueError: logger.warning(f"Data inválida (ValueError em strptime ou conversão int) para '{data_str_raw}'"); return data_str_raw
    else: logger.warning(f"Formato de data não reconhecido (não tem 3 partes): '{data_str_raw}'"); return data_str_raw