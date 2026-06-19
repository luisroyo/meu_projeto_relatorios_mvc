import logging
import re
from datetime import datetime, timedelta

from . import config
from .parser import (extrair_eventos_de_bloco,
                     extrair_eventos_de_mensagem_simples,
                     parse_linha_log_prefixo)
from .processing import parear_eventos_parada
from .report import formatar_relatorio_paradas
from .utils import normalizar_data_capturada

logger = logging.getLogger(__name__)


def calcular_intervalo_plantao(data_plantao_str: str, escala_plantao_str: str):
    """
    Calcula o datetime de início e fim do plantão.
    Retorna (datetime_inicio, datetime_fim, data_para_cabecalho_valida).
    """
    if not data_plantao_str or not escala_plantao_str:
        return None, None, config.FALLBACK_DATA_INDEFINIDA

    data_base_dt = None
    data_cabecalho = config.FALLBACK_DATA_INDEFINIDA
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


def processar_log_de_paradas(
    log_bruto_paradas_str: str,
    nome_condominio_str: str,
    data_plantao_manual_str: str = None,
    escala_plantao_str: str = None,
):
    logger.info(
        f"Processando log de paradas para: {nome_condominio_str}, Data Plantão: {data_plantao_manual_str}, Escala: {escala_plantao_str}"
    )
    if not log_bruto_paradas_str or not log_bruto_paradas_str.strip():
        logger.warning("Log de parada bruto está vazio.")
        return "Nenhum log de parada fornecido ou log vazio.", 0, None, None, 0

    inicio_intervalo_plantao, fim_intervalo_plantao, data_formatada_cabecalho = (
        calcular_intervalo_plantao(data_plantao_manual_str, escala_plantao_str)
    )

    if not inicio_intervalo_plantao or not fim_intervalo_plantao:
        logger.error(
            "Não foi possível determinar o intervalo do plantão. Processando sem filtro de data/hora."
        )

    log_processado = log_bruto_paradas_str.replace("\\[", "[").replace("\\]", "]")
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
        ultima_data_valida_global = config.FALLBACK_DATA_INDEFINIDA

    ultima_vtr_identificada_global = config.DEFAULT_VTR_ID
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
            lista_eventos_destino.extend(eventos_do_bloco)
            buffer.clear()

    for linha_raw in linhas:
        linha_strip = linha_raw.strip()
        if not linha_strip:
            continue

        hora_prefixo, data_prefixo, vtr_linha, mensagem_linha, vtr_contexto_proximas = (
            parse_linha_log_prefixo(linha_strip, ultima_vtr_identificada_global)
        )
        
        ultima_vtr_identificada_global = vtr_contexto_proximas

        if hora_prefixo and data_prefixo:
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

            ultima_data_valida_global = data_prefixo
            try:
                ultimo_datetime_log_global = datetime.strptime(
                    f"{data_prefixo} {hora_prefixo}", "%d/%m/%Y %H:%M"
                )
            except ValueError:
                logger.error(
                    f"Erro de formato ao analisar data/hora do prefixo: '{data_prefixo} {hora_prefixo}'"
                )
                ultimo_datetime_log_global = None

            eventos_mensagem_direta = extrair_eventos_de_mensagem_simples(
                mensagem_linha,
                data_prefixo,
                vtr_linha,
                linha_strip,
                ultimo_datetime_log_global,
                inicio_intervalo_plantao,
                fim_intervalo_plantao,
            )

            if eventos_mensagem_direta:
                eventos_encontrados_todos.extend(eventos_mensagem_direta)
            else:
                buffer_bloco_atual.append(mensagem_linha)
                vtr_para_contexto_bloco_atual = vtr_linha
                data_para_contexto_bloco_atual = data_prefixo
                linha_referencia_para_bloco_atual = linha_strip
                datetime_log_referencia_para_bloco_atual = (
                    ultimo_datetime_log_global
                )

        else:
            if buffer_bloco_atual:
                buffer_bloco_atual.append(linha_strip)
            else:
                eventos_sem_prefixo = extrair_eventos_de_mensagem_simples(
                    linha_strip,
                    ultima_data_valida_global,
                    vtr_linha,
                    linha_strip,
                    ultimo_datetime_log_global,
                    inicio_intervalo_plantao,
                    fim_intervalo_plantao,
                )
                if eventos_sem_prefixo:
                    eventos_encontrados_todos.extend(eventos_sem_prefixo)

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

    eventos_filtrados_plantao = []
    if inicio_intervalo_plantao and fim_intervalo_plantao:
        for ev in eventos_encontrados_todos:
            dt_ev = ev["datetime_obj"]
            if inicio_intervalo_plantao <= dt_ev < fim_intervalo_plantao:
                eventos_filtrados_plantao.append(ev)
            else:
                logger.info(
                    f"Filtro de plantão: Evento ignorado por estar fora do intervalo. "
                    f"Evento: {dt_ev.strftime('%d/%m/%Y %H:%M')} ({ev['tipo']}). "
                    f"Intervalo: {inicio_intervalo_plantao.strftime('%d/%m/%Y %H:%M')} a {fim_intervalo_plantao.strftime('%d/%m/%Y %H:%M')}"
                )
    else:
        eventos_filtrados_plantao = eventos_encontrados_todos

    eventos_filtrados_plantao.sort(key=lambda ev: ev["datetime_obj"])

    paradas_pareadas, alertas_pareamento, soma_duracao_total = parear_eventos_parada(
        eventos_filtrados_plantao
    )

    relatorio_texto_formatado = formatar_relatorio_paradas(
        nome_condominio_str,
        data_formatada_cabecalho,
        escala_plantao_str,
        eventos_filtrados_plantao,
        paradas_pareadas,
        alertas_pareamento,
    )

    primeiro_ev_dt = None
    ultimo_ev_dt = None
    if eventos_filtrados_plantao:
        primeiro_ev_dt = eventos_filtrados_plantao[0]["datetime_obj"]
        ultimo_ev_dt = eventos_filtrados_plantao[-1]["datetime_obj"]

    total_completas = sum(
        1 for r in paradas_pareadas if r.get("inicio_dt") and r.get("termino_dt")
    )

    return (
        relatorio_texto_formatado,
        total_completas,
        primeiro_ev_dt,
        ultimo_ev_dt,
        soma_duracao_total,
    )
