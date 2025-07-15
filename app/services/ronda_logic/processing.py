# app/services/ronda_logic/processing.py
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def parear_eventos_ronda(eventos: list):
    rondas_pareadas = []
    alertas_pareamento = []
    inicios_pendentes_por_vtr = {}

    # --- NOVO: Variável para acumular a duração ---
    soma_duracoes_minutos = 0

    for evento in eventos:
        if not evento.get("datetime_obj") or not isinstance(
            evento["datetime_obj"], datetime
        ):
            logger.warning(f"Evento inválido ou sem datetime_obj encontrado: {evento}.")
            alertas_pareamento.append(
                f"⚠️ Evento com dados inválidos ignorado: (Linha: '{evento.get('linha_original', 'N/A')}')"
            )
            continue

        vtr_evento = evento["vtr"]

        if evento["tipo"] == "inicio":
            inicio_pendente_vtr_atual = inicios_pendentes_por_vtr.get(vtr_evento)
            if inicio_pendente_vtr_atual:
                alertas_pareamento.append(
                    f"⚠️ Início de ronda para {inicio_pendente_vtr_atual['vtr']} às {inicio_pendente_vtr_atual['data_str']} {inicio_pendente_vtr_atual['hora_str']} "
                    f"sem término antes de novo início. (Linhas: '{inicio_pendente_vtr_atual['linha_original']}' e '{evento['linha_original']}')"
                )
                rondas_pareadas.append(
                    {
                        "inicio_dt": inicio_pendente_vtr_atual["datetime_obj"],
                        "termino_dt": None,
                        "vtr": inicio_pendente_vtr_atual["vtr"],
                    }
                )
            inicios_pendentes_por_vtr[vtr_evento] = evento

        elif evento["tipo"] == "termino":
            inicio_pendente_vtr_atual = inicios_pendentes_por_vtr.get(vtr_evento)
            if inicio_pendente_vtr_atual:
                inicio_dt = inicio_pendente_vtr_atual["datetime_obj"]
                termino_dt = evento["datetime_obj"]

                if termino_dt < inicio_dt:
                    if termino_dt.time() < inicio_dt.time():
                        termino_dt_ajustado = termino_dt + timedelta(days=1)
                        logger.info(
                            f"Aplicando heurística de cruzamento de dia para VTR {vtr_evento}. Término ajustado para {termino_dt_ajustado}."
                        )
                        termino_dt = termino_dt_ajustado

                duracao_minutos = 0  # Inicializa a duração
                if termino_dt > inicio_dt:
                    # --- NOVO: Cálculo e soma da duração ---
                    duracao_timedelta = termino_dt - inicio_dt
                    duracao_minutos = round(duracao_timedelta.total_seconds() / 60)
                    soma_duracoes_minutos += duracao_minutos
                else:
                    alertas_pareamento.append(
                        f"⚠️ ALERTA DE HORÁRIO: Término para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                        f"ocorreu ANTES ou no mesmo momento que o início. (Linhas: '{evento['linha_original']}' e '{inicio_pendente_vtr_atual['linha_original']}')"
                    )

                rondas_pareadas.append(
                    {
                        "inicio_dt": inicio_dt,
                        "termino_dt": termino_dt,
                        "vtr": vtr_evento,
                        "duracao_minutos": duracao_minutos,  # Adiciona a duração individual ao par
                    }
                )
                inicios_pendentes_por_vtr.pop(vtr_evento, None)
            else:
                alertas_pareamento.append(
                    f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} "
                    f"(Linha: '{evento['linha_original']}') sem início correspondente para esta VTR."
                )
                rondas_pareadas.append(
                    {
                        "inicio_dt": None,
                        "termino_dt": evento["datetime_obj"],
                        "vtr": evento["vtr"],
                    }
                )

    for vtr_id, inicio_pendente in inicios_pendentes_por_vtr.items():
        alertas_pareamento.append(
            f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} "
            f"(Linha: '{inicio_pendente['linha_original']}') sem término no final do log."
        )
        rondas_pareadas.append(
            {
                "inicio_dt": inicio_pendente["datetime_obj"],
                "termino_dt": None,
                "vtr": inicio_pendente["vtr"],
            }
        )

    # --- ALTERADO: Retorna 3 valores, incluindo a soma dos minutos ---
    return rondas_pareadas, alertas_pareamento, soma_duracoes_minutos
