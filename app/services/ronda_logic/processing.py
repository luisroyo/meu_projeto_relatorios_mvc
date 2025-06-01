import logging
from datetime import datetime # Necessário para isinstance

logger = logging.getLogger(__name__)

def parear_eventos_ronda(eventos: list):
    rondas_pareadas = []
    alertas_pareamento = []
    inicio_pendente = None

    for evento in eventos:
        # Validação básica do evento - deve ter datetime_obj
        if not evento.get("datetime_obj") or not isinstance(evento["datetime_obj"], datetime):
            logger.warning(f"Evento inválido ou sem datetime_obj encontrado durante o pareamento: {evento}. Pulando.")
            alertas_pareamento.append(f"⚠️ Evento com dados inválidos ou hora incorreta detectado e ignorado: (Linha: '{evento.get('linha_original', 'N/A')}')")
            continue # Pula para o próximo evento

        if evento["tipo"] == "inicio":
            if inicio_pendente:
                # Verifica se o início pendente é da mesma VTR do novo início
                if inicio_pendente["vtr"] == evento["vtr"]:
                    alertas_pareamento.append(
                        f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} "
                        f"(Linha: '{inicio_pendente['linha_original']}') sem término correspondente antes de novo início "
                        f"(Linha: '{evento['linha_original']}')."
                    )
                    # Adiciona o início pendente como uma ronda incompleta
                    rondas_pareadas.append({
                        "inicio_dt": inicio_pendente["datetime_obj"],
                        "termino_dt": None,
                        "vtr": inicio_pendente["vtr"]
                    })
                # Se as VTRs são diferentes, o início pendente de uma VTR não impede o início de outra.
                # No entanto, se o comportamento desejado é que qualquer início pendente gere alerta
                # ao encontrar um novo início, a condição `elif` abaixo pode ser removida ou ajustada.
                # Por ora, manteremos a lógica de que um início pendente só é problemático
                # se um novo início da MESMA VTR for encontrado.
                # Para o alerta de VTR diferente, a lógica original era:
                # elif inicio_pendente["vtr"] != evento["vtr"]:
                # alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') ainda pendente ao encontrar início de {evento['vtr']}.")
                # Esta lógica acima foi removida pois um novo início de VTR diferente não "fecha" o anterior. O anterior continua pendente.

            # Define o novo evento de início como pendente
            inicio_pendente = evento

        elif evento["tipo"] == "termino":
            if inicio_pendente:
                if inicio_pendente["vtr"] == evento["vtr"]:
                    # Validação cronológica
                    if evento["datetime_obj"] <= inicio_pendente["datetime_obj"]:
                        alertas_pareamento.append(
                            f"⚠️ ALERTA DE HORÁRIO: Término para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                            f"(Linha: '{evento['linha_original']}') ocorreu ANTES ou NO MESMO MOMENTO que o início "
                            f"às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} "
                            f"(Linha: '{inicio_pendente['linha_original']}')."
                        )
                        # Adiciona a ronda com os horários problemáticos para que seja visível
                        rondas_pareadas.append({
                            "inicio_dt": inicio_pendente["datetime_obj"],
                            "termino_dt": evento["datetime_obj"], # Horário de término problemático
                            "vtr": inicio_pendente["vtr"],
                            "alerta_cronologico": True # Flag para possível destaque no relatório
                        })
                    else: # Horários cronologicamente corretos
                        rondas_pareadas.append({
                            "inicio_dt": inicio_pendente["datetime_obj"],
                            "termino_dt": evento["datetime_obj"],
                            "vtr": inicio_pendente["vtr"]
                        })
                    inicio_pendente = None # Limpa o início pendente, pois foi pareado
                else: # Término encontrado, mas VTR não corresponde ao início pendente
                    alertas_pareamento.append(
                        f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                        f"(Linha: '{evento['linha_original']}') mas início pendente era de {inicio_pendente['vtr']} "
                        f"(Linha: '{inicio_pendente['linha_original']}'). O início de {inicio_pendente['vtr']} continua pendente."
                    )
                    # Adiciona o término como uma ronda "órfã" (sem início correspondente nesta lógica de pareamento)
                    rondas_pareadas.append({
                        "inicio_dt": None,
                        "termino_dt": evento["datetime_obj"],
                        "vtr": evento["vtr"]
                    })
            else: # Término encontrado sem nenhum início pendente
                alertas_pareamento.append(
                    f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                    f"(Linha: '{evento['linha_original']}') sem início correspondente."
                )
                rondas_pareadas.append({
                    "inicio_dt": None,
                    "termino_dt": evento["datetime_obj"],
                    "vtr": evento["vtr"]
                })

    # Se, após processar todos os eventos, ainda houver um início pendente
    if inicio_pendente:
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