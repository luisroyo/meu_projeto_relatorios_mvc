import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def inferir_turno(data_plantao_obj, escala_plantao_str):
    """Inferir se o turno é Noturno Par, Noturno Impar, Diurno Par ou Diurno Impar baseado na escala e paridade do dia."""
    escala_lower = escala_plantao_str.lower().strip() if escala_plantao_str else ""
    dia = data_plantao_obj.day if data_plantao_obj else datetime.now(timezone.utc).day
    paridade = "Par" if dia % 2 == 0 else "Impar"
    logger.info(f"[DEBUG INFERIR_TURNO] escala_plantao_str='{escala_plantao_str}', escala_lower='{escala_lower}', dia={dia}, paridade={paridade}")
    if escala_lower.startswith("06h"):
        turno = f"Diurno {paridade}"
    elif escala_lower.startswith("18h"):
        turno = f"Noturno {paridade}"
    else:
        turno = f"Noturno {paridade}"
    logger.info(f"[DEBUG INFERIR_TURNO] Retornando turno: '{turno}'")
    return turno 