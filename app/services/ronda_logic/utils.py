import logging

logger = logging.getLogger(__name__)

def normalizar_hora_capturada(hora_str_raw: str) -> str:
    """Normaliza uma string de hora capturada (ex: '18 : 48', '7:00') para HH:MM."""
    if hora_str_raw is None:
        return ""
    hora_str_limpa = "".join(hora_str_raw.split())
    if ":" not in hora_str_limpa:
        if len(hora_str_limpa) == 3 and hora_str_limpa.isdigit():
            hora_str_limpa = f"0{hora_str_limpa[0]}:{hora_str_limpa[1:]}"
        elif len(hora_str_limpa) == 4 and hora_str_limpa.isdigit():
            hora_str_limpa = f"{hora_str_limpa[:2]}:{hora_str_limpa[2:]}"
        else:
            logger.warning(f"Formato de hora sem ':' e não numérico esperado: '{hora_str_raw}'")
            return hora_str_raw
    
    parts = hora_str_limpa.split(':')
    if len(parts) == 2:
        try:
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                logger.warning(f"Valores de hora/minuto fora do intervalo: '{hora_str_raw}' -> H:{h}, M:{m}")
                return hora_str_raw
            return f"{h:02d}:{m:02d}"
        except ValueError:
            logger.warning(f"Formato de hora inválido após limpeza inicial: '{hora_str_limpa}'")
            return hora_str_raw
    logger.warning(f"Formato de hora não reconhecido para normalização: '{hora_str_raw}'")
    return hora_str_raw