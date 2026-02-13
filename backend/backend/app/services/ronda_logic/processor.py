# app/services/ronda_logic/processor.py
import logging
import re
from datetime import datetime, timedelta

from .config import FALLBACK_DATA_INDEFINIDA, DEFAULT_VTR_ID
from .parser import (extrair_eventos_de_bloco,
                     extrair_eventos_de_mensagem_simples,
                     parse_linha_log_prefixo)
from .processing import parear_eventos_ronda
from .report import formatar_relatorio_rondas
from .utils import normalizar_data_capturada

logger = logging.getLogger(__name__)


def calcular_intervalo_plantao(data_plantao_str: str, escala_plantao_str: str):
    """
    Calcula o datetime de início e fim do plantão.
    A data de entrada é SEMPRE considerada a DATA DE INÍCIO do plantão.
    Retorna (datetime_inicio, datetime_fim, data_para_cabecalho_valida).
    """
    if not data_plantao_str or not escala_plantao_str:
        return None, None, FALLBACK_DATA_INDEFINIDA

    data_base_dt = None
    data_cabecalho = FALLBACK_DATA_INDEFINIDA
    try:
        data_norm = normalizar_data_capturada(data_plantao_str)
        if not data_norm or len(data_norm.split("/")[2]) != 4:
            raise ValueError("Data normalizada inválida ou ano não tem 4 dígitos")
        data_base_dt = datetime.strptime(data_norm, "%d/%m/%Y")
        data_cabecalho = data_norm
    except ValueError as e:
        logger.error(
            f"Data de plantão manual ('{data_plantao_str}') inválida: {e}. Não é possível calcular intervalo."
        )
        return None, None, data_plantao_str

    escala_normalizada_para_parse = escala_plantao_str.strip()
    match_escala_humanizada = re.match(
        r"(\d{1,2})h\s*às\s*(\d{1,2})h", escala_normalizada_para_parse, re.IGNORECASE
    )
    if match_escala_humanizada:
        escala_normalizada_para_parse = (
            f"{match_escala_humanizada.group(1)}-{match_escala_humanizada.group(2)}"
        )
        logger.info(
            f"Escala '{escala_plantao_str}' normalizada para '{escala_normalizada_para_parse}' para processamento."
        )

    partes_escala = escala_normalizada_para_parse.split("-")
    if len(partes_escala) != 2:
        logger.error(
            f"Escala de plantão ('{escala_plantao_str}') inválida. Use formato HH-MM ou HHh às MMh."
        )
        return None, None, data_cabecalho

    try:
        hora_inicio_escala = int(partes_escala[0])
        hora_fim_escala = int(partes_escala[1])
    except ValueError:
        logger.error(
            f"Horas da escala ('{escala_normalizada_para_parse}') não são numéricas."
        )
        return None, None, data_cabecalho

    inicio_plantao = data_base_dt.replace(
        hour=hora_inicio_escala, minute=0, second=0, microsecond=0
    )

    data_para_cabecalho_valida = data_cabecalho

    if hora_inicio_escala < hora_fim_escala:
        fim_plantao = data_base_dt.replace(
            hour=hora_fim_escala, minute=0, second=0, microsecond=0
        )
    else:
        fim_plantao_dia_seguinte = data_base_dt + timedelta(days=1)
        fim_plantao = fim_plantao_dia_seguinte.replace(
            hour=hora_fim_escala, minute=0, second=0, microsecond=0
        )

    logger.info(
        f"Intervalo de plantão calculado: de {inicio_plantao.strftime('%d/%m/%Y %H:%M')} a {fim_plantao.strftime('%d/%m/%Y %H:%M')}"
    )
    return inicio_plantao, fim_plantao, data_para_cabecalho_valida


def processar_log_de_rondas(
    log_bruto_rondas_str: str,
    nome_condominio_str: str,
    data_plantao_manual_str: str = None,
    escala_plantao_str: str = None,
):
    logger.info(
        f"Processando log para: {nome_condominio_str}, Data Plantão: {data_plantao_manual_str}, Escala: {escala_plantao_str}"
    )
    if not log_bruto_rondas_str or not log_bruto_rondas_str.strip():
        logger.warning("Log de ronda bruto está vazio.")
        # Retorna 5 valores, com 0 para os numéricos
        return "Nenhum log de ronda fornecido ou log vazio.", 0, None, None, 0

    inicio_intervalo_plantao, fim_intervalo_plantao, data_formatada_cabecalho = (
        calcular_intervalo_plantao(data_plantao_manual_str, escala_plantao_str)
    )

    if not inicio_intervalo_plantao or not fim_intervalo_plantao:
        logger.error(
            "Não foi possível determinar o intervalo do plantão. Processando sem filtro de data/hora."
        )

    log_processado = log_bruto_rondas_str.replace("\\[", "[").replace("\\]", "]")
    linhas = log_processado.strip().split("\n")

    eventos_encontrados_todos = []

    data_manual_normalizada = (
        normalizar_data_capturada(data_plantao_manual_str)
        if data_plantao_manual_str
        else None
    )
    if data_manual_normalizada:
        ultima_data_valida_global = data_manual_normalizada
    else:
        ultima_data_valida_global = FALLBACK_DATA_INDEFINIDA

    ultima_vtr_identificada_global = DEFAULT_VTR_ID
    ultimo_datetime_log_global = None
    buffer_bloco_atual = []
    vtr_para_contexto_bloco_atual = ultima_vtr_identificada_global
    data_para_contexto_bloco_atual = ultima_data_valida_global
    linha_referencia_para_bloco_atual = ""
    datetime_log_referencia_para_bloco_atual = None

    def processar_buffer_bloco_se_existente(
        buffer,
        vtr_ctx,
        data_ctx,
        ref_linha,
        ref_dt_log,
        lista_eventos_destino,
        inicio_plantao,
        fim_plantao,
    ):
        if buffer:
            eventos_do_bloco = extrair_eventos_de_bloco(
                buffer,
                vtr_ctx,
                data_ctx,
                ref_linha,
                ref_dt_log,
                inicio_plantao,
                fim_plantao,
            )
            if eventos_do_bloco:
                lista_eventos_destino.extend(eventos_do_bloco)
            buffer.clear()

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip:
            continue

        hora_log_raw, data_prefixo, vtr_linha, msg_linha, vtr_global = (
            parse_linha_log_prefixo(linha_strip, ultima_vtr_identificada_global)
        )

        current_log_entry_datetime = None
        data_log_ctx = ultima_data_valida_global
        if data_prefixo:
            data_log_ctx = data_prefixo

        if (
            data_log_ctx
            and data_log_ctx != FALLBACK_DATA_INDEFINIDA
            and hora_log_raw
        ):
            try:
                current_log_entry_datetime = datetime.strptime(
                    f"{data_log_ctx} {hora_log_raw}", "%d/%m/%Y %H:%M"
                )
                ultimo_datetime_log_global = current_log_entry_datetime
            except ValueError:
                logger.warning(
                    f"Não foi possível criar datetime da entrada de log: data='{data_log_ctx}', hora='{hora_log_raw}'"
                )
        else:
            current_log_entry_datetime = ultimo_datetime_log_global

        if data_prefixo:
            processar_buffer_bloco_se_existente(
                buffer_bloco_atual,
                vtr_para_contexto_bloco_atual,
                data_para_contexto_bloco_atual,
                linha_referencia_para_bloco_atual,
                datetime_log_referencia_para_bloco_atual,
                eventos_encontrados_todos,
                inicio_intervalo_plantao,
                fim_intervalo_plantao,
            )

            ultima_vtr_identificada_global = vtr_global
            if data_prefixo and data_prefixo != FALLBACK_DATA_INDEFINIDA:
                ultima_data_valida_global = data_prefixo

            vtr_para_contexto_bloco_atual = vtr_linha
            data_para_contexto_bloco_atual = ultima_data_valida_global
            linha_referencia_para_bloco_atual = linha_original
            datetime_log_referencia_para_bloco_atual = current_log_entry_datetime

            if msg_linha:
                eventos_msg_simples = extrair_eventos_de_mensagem_simples(
                    msg_linha,
                    ultima_data_valida_global,
                    vtr_linha,
                    linha_original,
                    current_log_entry_datetime,
                    inicio_intervalo_plantao,
                    fim_intervalo_plantao,
                )
                if eventos_msg_simples:
                    eventos_encontrados_todos.extend(eventos_msg_simples)
        else:
            buffer_bloco_atual.append(msg_linha)

    processar_buffer_bloco_se_existente(
        buffer_bloco_atual,
        vtr_para_contexto_bloco_atual,
        data_para_contexto_bloco_atual,
        linha_referencia_para_bloco_atual,
        datetime_log_referencia_para_bloco_atual,
        eventos_encontrados_todos,
        inicio_intervalo_plantao,
        fim_intervalo_plantao,
    )

    eventos_do_plantao = [
        ev for ev in eventos_encontrados_todos if ev.get("datetime_obj")
    ]
    if inicio_intervalo_plantao and fim_intervalo_plantao:
        eventos_do_plantao = [
            ev
            for ev in eventos_do_plantao
            if inicio_intervalo_plantao <= ev["datetime_obj"] < fim_intervalo_plantao
        ]

    if not eventos_do_plantao:
        # ... (lógica de mensagem de retorno) ...
        # Retorna 5 valores
        return "Nenhum evento de ronda ...", 0, None, None, 0

    eventos_do_plantao.sort(key=lambda x: x["datetime_obj"])
    primeiro_evento_dt = eventos_do_plantao[0]["datetime_obj"]
    ultimo_evento_dt = eventos_do_plantao[-1]["datetime_obj"]

    logger.info(
        f"Total de {len(eventos_do_plantao)} eventos encontrados DENTRO do intervalo do plantão."
    )

    # --- ALTERADO: Recebe 3 valores da função de pareamento ---
    rondas_pareadas, alertas_pareamento, soma_minutos = parear_eventos_ronda(
        eventos_do_plantao
    )

    if not rondas_pareadas and not alertas_pareamento:
        # Retorna 5 valores
        return (
            "Eventos de ronda identificados, mas insuficientes para formar pares ou gerar alertas.",
            0,
            primeiro_evento_dt,
            ultimo_evento_dt,
            0,
        )

    relatorio_final = formatar_relatorio_rondas(
        nome_condominio_str,
        data_formatada_cabecalho,
        escala_plantao_str,
        eventos_encontrados_todos,
        rondas_pareadas,
        alertas_pareamento,
    )
    rondas_completas_count = sum(
        1 for r in rondas_pareadas if r.get("inicio_dt") and r.get("termino_dt")
    )
    logger.info(
        f"Relatório para {nome_condominio_str} formatado. {len(eventos_do_plantao)} eventos, {rondas_completas_count} rondas completas."
    )

    # --- ALTERADO: Retorna 5 valores, incluindo a soma dos minutos ---
    return (
        relatorio_final,
        rondas_completas_count,
        primeiro_evento_dt,
        ultimo_evento_dt,
        soma_minutos,
    )
