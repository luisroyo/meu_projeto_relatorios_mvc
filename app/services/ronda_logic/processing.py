import logging
from datetime import datetime # Necessário para isinstance

logger = logging.getLogger(__name__)

def parear_eventos_ronda(eventos: list):
    rondas_pareadas = []
    alertas_pareamento = []
    # Dicionário para rastrear inícios pendentes por VTR
    inicios_pendentes_por_vtr = {} # Chave: id_vtr, Valor: evento de inicio

    for evento in eventos:
        # Validação básica do evento - deve ter datetime_obj
        if not evento.get("datetime_obj") or not isinstance(evento["datetime_obj"], datetime):
            logger.warning(f"Evento inválido ou sem datetime_obj encontrado durante o pareamento: {evento}. Pulando.")
            alertas_pareamento.append(f"⚠️ Evento com dados inválidos ou hora incorreta detectado e ignorado: (Linha: '{evento.get('linha_original', 'N/A')}')")
            continue 

        vtr_evento = evento["vtr"]

        if evento["tipo"] == "inicio":
            inicio_pendente_vtr_atual = inicios_pendentes_por_vtr.get(vtr_evento)
            if inicio_pendente_vtr_atual:
                # Já existe um início pendente para esta VTR
                alertas_pareamento.append(
                    f"⚠️ Início de ronda para {inicio_pendente_vtr_atual['vtr']} às {inicio_pendente_vtr_atual['data_str']} {inicio_pendente_vtr_atual['hora_str']} "
                    f"(Linha: '{inicio_pendente_vtr_atual['linha_original']}') sem término correspondente antes de novo início "
                    f"(Linha: '{evento['linha_original']}')."
                )
                # Adiciona o início pendente como uma ronda incompleta
                rondas_pareadas.append({
                    "inicio_dt": inicio_pendente_vtr_atual["datetime_obj"],
                    "termino_dt": None,
                    "vtr": inicio_pendente_vtr_atual["vtr"]
                })
            
            # Define o novo evento de início como pendente para esta VTR
            inicios_pendentes_por_vtr[vtr_evento] = evento

        elif evento["tipo"] == "termino":
            inicio_pendente_vtr_atual = inicios_pendentes_por_vtr.get(vtr_evento)
            if inicio_pendente_vtr_atual:
                # Validação cronológica
                if evento["datetime_obj"] <= inicio_pendente_vtr_atual["datetime_obj"]:
                    alertas_pareamento.append(
                        f"⚠️ ALERTA DE HORÁRIO: Término para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                        f"(Linha: '{evento['linha_original']}') ocorreu ANTES ou NO MESMO MOMENTO que o início "
                        f"às {inicio_pendente_vtr_atual['data_str']} {inicio_pendente_vtr_atual['hora_str']} "
                        f"(Linha: '{inicio_pendente_vtr_atual['linha_original']}')."
                    )
                    # Adiciona a ronda com os horários problemáticos
                    rondas_pareadas.append({
                        "inicio_dt": inicio_pendente_vtr_atual["datetime_obj"],
                        "termino_dt": evento["datetime_obj"], 
                        "vtr": inicio_pendente_vtr_atual["vtr"],
                        "alerta_cronologico": True 
                    })
                else: # Horários cronologicamente corretos
                    rondas_pareadas.append({
                        "inicio_dt": inicio_pendente_vtr_atual["datetime_obj"],
                        "termino_dt": evento["datetime_obj"],
                        "vtr": inicio_pendente_vtr_atual["vtr"]
                    })
                # Limpa o início pendente desta VTR, pois foi pareado
                inicios_pendentes_por_vtr.pop(vtr_evento, None) 
            else: # Término encontrado sem nenhum início pendente para esta VTR
                alertas_pareamento.append(
                    f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                    f"(Linha: '{evento['linha_original']}') sem início correspondente para esta VTR."
                )
                rondas_pareadas.append({
                    "inicio_dt": None,
                    "termino_dt": evento["datetime_obj"],
                    "vtr": evento["vtr"]
                })

    # Após processar todos os eventos, verifica se ainda há inícios pendentes para qualquer VTR
    for vtr_id, inicio_pendente in inicios_pendentes_por_vtr.items():
        if inicio_pendente: # Segurança, mas deve sempre existir se estiver no dict
            alertas_pareamento.append(
                f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} "
                f"(Linha: '{inicio_pendente['linha_original']}') sem término correspondente no final do log."
            )
            rondas_pareadas.append({
                "inicio_dt": inicio_pendente["datetime_obj"],
                "termino_dt": None,
                "vtr": inicio_pendente["vtr"]
            })
    return rondas_pareadas, alertas_pareamento