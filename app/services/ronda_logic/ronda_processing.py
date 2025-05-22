import logging
# datetime não é usado diretamente, mas pode ser útil para type hints se desejar
# from datetime import datetime 

logger = logging.getLogger(__name__)

def parear_eventos_ronda(eventos: list):
    """Realiza o pareamento de eventos de início e término de rondas."""
    rondas_pareadas = []
    alertas_pareamento = []
    inicio_pendente = None

    for evento in eventos: # eventos já devem estar ordenados por datetime_obj
        if evento["tipo"] == "inicio":
            if inicio_pendente:
                if inicio_pendente["vtr"] == evento["vtr"]:
                    alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') sem término correspondente antes de novo início (Linha: '{evento['linha_original']}').")
                    rondas_pareadas.append({"inicio_dt": inicio_pendente["datetime_obj"], "termino_dt": None, "vtr": inicio_pendente["vtr"]})
                elif inicio_pendente["vtr"] != evento["vtr"]:
                     alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') ainda pendente ao encontrar início de {evento['vtr']}.")
            inicio_pendente = evento
        elif evento["tipo"] == "termino":
            if inicio_pendente:
                if inicio_pendente["vtr"] == evento["vtr"]: 
                    rondas_pareadas.append({"inicio_dt": inicio_pendente["datetime_obj"], "termino_dt": evento["datetime_obj"], "vtr": inicio_pendente["vtr"]})
                    inicio_pendente = None
                else: 
                    alertas_pareamento.append(f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} (Linha: '{evento['linha_original']}') mas início pendente era de {inicio_pendente['vtr']} (Linha: '{inicio_pendente['linha_original']}').")
                    rondas_pareadas.append({ "inicio_dt": None, "termino_dt": evento["datetime_obj"], "vtr": evento["vtr"] })
            else: 
                alertas_pareamento.append(f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} (Linha: '{evento['linha_original']}') sem início correspondente.")
                rondas_pareadas.append({ "inicio_dt": None, "termino_dt": evento["datetime_obj"], "vtr": evento["vtr"] })

    if inicio_pendente: 
        alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') sem término correspondente no final do log.")
        rondas_pareadas.append({ "inicio_dt": inicio_pendente["datetime_obj"], "termino_dt": None, "vtr": inicio_pendente["vtr"] })
    return rondas_pareadas, alertas_pareamento