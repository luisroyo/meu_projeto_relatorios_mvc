# utils.py
import logging
import re

logger = logging.getLogger(__name__)

def normalizar_hora_capturada(hora_str_raw: str) -> str:
    """Normaliza uma string de hora capturada para HH:MM."""
    if hora_str_raw is None:
        logger.warning("Tentativa de normalizar hora_str_raw que é None.")
        return "" # Retorna string vazia para evitar erros posteriores, ou poderia ser None.

    hora_str_trabalho = str(hora_str_raw).strip().lower() # Converte para str, remove espaços e para minúsculas

    # Tenta remover "hs", "hrs" do final, se presentes
    if hora_str_trabalho.endswith("hs"):
        hora_str_trabalho = hora_str_trabalho[:-2].strip()
    elif hora_str_trabalho.endswith("hrs"):
        hora_str_trabalho = hora_str_trabalho[:-3].strip()


    # Padrão para HHhMM (ex: 06h30, 18h00) ou HHh (ex: 6h, 18h)
    match_h_format = re.fullmatch(r"(\d{1,2})h(\d{2})?", hora_str_trabalho)
    if match_h_format:
        h_str = match_h_format.group(1)
        m_str = match_h_format.group(2) if match_h_format.group(2) else "00" # Se só HHh, assume :00
        try:
            h, m = int(h_str), int(m_str)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
            else:
                logger.warning(f"Valores de hora/minuto fora do intervalo em formato 'h': '{hora_str_raw}' -> H:{h}, M:{m}")
                return hora_str_raw # Retorna original se inválido
        except ValueError:
            logger.warning(f"Formato 'h' inválido (não numérico) após match: '{hora_str_raw}'")
            return hora_str_raw

    # Remove todos os espaços para formatos como "18 : 48" -> "18:48"
    hora_str_limpa = "".join(hora_str_trabalho.split())

    # Formatos numéricos diretos: HMM, HHMM (ex: 700 -> 07:00, 1800 -> 18:00)
    if ":" not in hora_str_limpa and "h" not in hora_str_limpa and hora_str_limpa.isdigit():
        if len(hora_str_limpa) == 3: # HMM
            h_str, m_str = hora_str_limpa[0], hora_str_limpa[1:]
            hora_str_limpa = f"0{h_str}:{m_str}"
        elif len(hora_str_limpa) == 4: # HHMM
            h_str, m_str = hora_str_limpa[:2], hora_str_limpa[2:]
            hora_str_limpa = f"{h_str}:{m_str}"
        # Se for 1 ou 2 dígitos, pode ser apenas a hora (ex: 7, 18), assumir :00
        elif len(hora_str_limpa) == 1: # H
             hora_str_limpa = f"0{hora_str_limpa}:00"
        elif len(hora_str_limpa) == 2: # HH
             hora_str_limpa = f"{hora_str_limpa}:00"
        else:
            logger.warning(f"Formato de hora numérico não esperado: '{hora_str_raw}' (limpo: '{hora_str_limpa}')")
            return hora_str_raw # Retorna original

    # Formato HH:MM (após limpezas e transformações)
    parts = hora_str_limpa.split(':')
    if len(parts) == 2:
        try:
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
            else:
                logger.warning(f"Valores de hora/minuto fora do intervalo: '{hora_str_raw}' -> H:{h}, M:{m}")
                return hora_str_raw # Retorna original
        except ValueError: # Se h ou m não forem inteiros
            logger.warning(f"Formato de hora inválido (não numérico) após split por ':': '{hora_str_limpa}' (original: '{hora_str_raw}')")
            return hora_str_raw
            
    logger.warning(f"Formato de hora não reconhecido para normalização: '{hora_str_raw}' (processado como: '{hora_str_trabalho}')")
    return hora_str_raw # Retorna original se nenhuma regra normalizou