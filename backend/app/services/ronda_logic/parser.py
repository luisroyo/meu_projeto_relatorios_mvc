# app/services/ronda_logic/parser.py
import logging
import re
import unicodedata
from datetime import datetime, timedelta

from . import config
from .utils import normalizar_data_capturada, normalizar_hora_capturada

logger = logging.getLogger(__name__)


def _limpar_e_normalizar_mensagem(texto: str) -> str:
    if not texto:
        return ""
    texto_normalizado = unicodedata.normalize("NFC", texto)
    texto_com_espacos_padronizados = re.sub(r"\s+", " ", texto_normalizado)
    return texto_com_espacos_padronizados.strip()


def parse_linha_log_prefixo(linha_strip: str, ultima_vtr_conhecida_global: str):
    hora_linha_log_raw = None
    data_linha_original = None
    mensagem_eventos = linha_strip
    id_vtr_para_eventos_desta_linha = ultima_vtr_conhecida_global
    vtr_contexto_geral_para_proximas_linhas = ultima_vtr_conhecida_global

    # --- NOVO: Verificar se é uma linha simples de VTR ---
    match_vtr_simples = config.REGEX_VTR_LINHA_SIMPLES.match(linha_strip)
    if match_vtr_simples:
        vtr_especifica_da_linha = match_vtr_simples.group(1).upper().replace(" ", "")
        id_vtr_para_eventos_desta_linha = vtr_especifica_da_linha
        vtr_contexto_geral_para_proximas_linhas = vtr_especifica_da_linha
        return (
            None,
            None,
            id_vtr_para_eventos_desta_linha,
            "",  # Linha de VTR não tem mensagem de evento
            vtr_contexto_geral_para_proximas_linhas,
        )

    match_prefixo = config.REGEX_PREFIXO_LINHA.match(linha_strip)
    if match_prefixo:
        hora_linha_log_raw_temp = match_prefixo.group(1)
        data_str_raw = match_prefixo.group(2)
        hora_linha_log_raw = normalizar_hora_capturada(hora_linha_log_raw_temp)
        data_linha_original = normalizar_data_capturada(data_str_raw)
        vtr_do_prefixo_str = match_prefixo.group(3)
        mensagem_eventos = match_prefixo.group(4).strip()
        vtr_do_prefixo_normalizada = None
        if vtr_do_prefixo_str:
            vtr_do_prefixo_normalizada = vtr_do_prefixo_str.upper().replace(" ", "")
            vtr_contexto_geral_para_proximas_linhas = vtr_do_prefixo_normalizada
            id_vtr_para_eventos_desta_linha = vtr_do_prefixo_normalizada
        match_vtr_na_mensagem = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(
            mensagem_eventos
        )
        if match_vtr_na_mensagem:
            vtr_especifica_da_mensagem = (
                match_vtr_na_mensagem.group(1).upper().replace(" ", "")
            )
            id_vtr_para_eventos_desta_linha = vtr_especifica_da_mensagem
            mensagem_eventos = match_vtr_na_mensagem.group(2).strip()
            vtr_contexto_geral_para_proximas_linhas = id_vtr_para_eventos_desta_linha
        return (
            hora_linha_log_raw,
            data_linha_original,
            id_vtr_para_eventos_desta_linha,
            _limpar_e_normalizar_mensagem(mensagem_eventos),
            vtr_contexto_geral_para_proximas_linhas,
        )

    
    # --- NOVO: Tentar Regex sem colchetes ---
    match_sem_colchetes = config.REGEX_PREFIXO_LINHA_SEM_COLCHETES.match(linha_strip)
    if match_sem_colchetes:
        data_str_raw = match_sem_colchetes.group(1)
        hora_linha_log_raw_temp = match_sem_colchetes.group(2)
        vtr_do_prefixo_str = match_sem_colchetes.group(3)
        mensagem_eventos = match_sem_colchetes.group(4).strip()

        hora_linha_log_raw = normalizar_hora_capturada(hora_linha_log_raw_temp)
        data_linha_original = normalizar_data_capturada(data_str_raw)

        if vtr_do_prefixo_str:
            # Tenta limpar o sender para ver se é uma VTR ou se é apenas um nome
            # Se contiver "VTR" ou "Águia", tratamos como VTR.
            # Caso contrário, mantemos a última VTR conhecida (pois pode ser mensagem de supervisor)
            if re.search(r"(VTR|Águia)", vtr_do_prefixo_str, re.IGNORECASE):
                vtr_normalizada = vtr_do_prefixo_str.upper().replace(" ", "")
                # Extrai apenas a parte da VTR se houver lixo (ex: "Douglas Supervisor Líder: 00:45 VTR 09 Felipe")
                match_vtr_clean = re.search(r"(VTR\s*\d+|Águia\s*\d+)", vtr_do_prefixo_str, re.IGNORECASE)
                if match_vtr_clean:
                    vtr_normalizada = match_vtr_clean.group(1).upper().replace(" ", "")
                
                vtr_contexto_geral_para_proximas_linhas = vtr_normalizada
                id_vtr_para_eventos_desta_linha = vtr_normalizada
            else:
                # Se o sender não parece VTR (ex: Supervisor), verificamos se a mensagem começa com VTR
                pass 
        
        # Verifica se há VTR no início da mensagem (comum quando o sender é o supervisor)
        match_vtr_na_mensagem = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(mensagem_eventos)
        if match_vtr_na_mensagem:
            vtr_especifica_da_mensagem = match_vtr_na_mensagem.group(1).upper().replace(" ", "")
            id_vtr_para_eventos_desta_linha = vtr_especifica_da_mensagem
            mensagem_eventos = match_vtr_na_mensagem.group(2).strip()
            vtr_contexto_geral_para_proximas_linhas = id_vtr_para_eventos_desta_linha

        return (
            hora_linha_log_raw,
            data_linha_original,
            id_vtr_para_eventos_desta_linha,
            _limpar_e_normalizar_mensagem(mensagem_eventos),
            vtr_contexto_geral_para_proximas_linhas,
        )

    else:
        return (
            None,
            None,
            ultima_vtr_conhecida_global,
            _limpar_e_normalizar_mensagem(linha_strip),
            ultima_vtr_conhecida_global,
        )


def _ajustar_data_evento_para_plantao(
    dt_obj, data_str_original, inicio_plantao, fim_plantao, log_entry_datetime=None
):
    """Ajusta a data de um evento para caber no plantão, se necessário."""
    # Heurística 1: Ajuste de dia com base no intervalo do plantão (mais robusta)
    if inicio_plantao and fim_plantao:
        if not (inicio_plantao <= dt_obj < fim_plantao):
            dt_obj_dia_anterior = dt_obj - timedelta(days=1)
            dt_obj_dia_seguinte = dt_obj + timedelta(days=1)
            if inicio_plantao <= dt_obj_dia_anterior < fim_plantao:
                logger.info(
                    f"Heurística de intervalo: Ajustando data do evento para o dia anterior. Original: {dt_obj}, Ajustado: {dt_obj_dia_anterior}"
                )
                return dt_obj_dia_anterior
            elif inicio_plantao <= dt_obj_dia_seguinte < fim_plantao:
                logger.info(
                    f"Heurística de intervalo: Ajustando data do evento para o dia seguinte. Original: {dt_obj}, Ajustado: {dt_obj_dia_seguinte}"
                )
                return dt_obj_dia_seguinte

    # Heurística 2: Baseada no timestamp do log (fallback)
    if (
        log_entry_datetime
        and log_entry_datetime.time().hour < 7
        and dt_obj.time().hour >= 18
    ):
        if dt_obj.date() == log_entry_datetime.date():
            dt_obj_ajustado = dt_obj - timedelta(days=1)
            if not (inicio_plantao and fim_plantao) or (
                inicio_plantao <= dt_obj_ajustado < fim_plantao
            ):
                logger.info(
                    f"Heurística de timestamp: Ajustando data do evento para dia anterior. Original: {dt_obj}, Ajustado: {dt_obj_ajustado}"
                )
                return dt_obj_ajustado

    return dt_obj  # Retorna o objeto original se nenhum ajuste for necessário


def extrair_eventos_de_mensagem_simples(
    mensagem_raw: str,
    data_log_contexto: str,
    id_vtr_contexto: str,
    linha_original_str: str,
    log_entry_datetime: datetime = None,
    inicio_plantao: datetime = None,
    fim_plantao: datetime = None,
):
    if (
        not mensagem_raw
        or not data_log_contexto
        or data_log_contexto == config.FALLBACK_DATA_INDEFINIDA
    ):
        return []
    mensagem = _limpar_e_normalizar_mensagem(mensagem_raw)

    for r_info in config.COMPILED_RONDA_EVENT_REGEXES:
        match_evento = r_info["regex"].search(mensagem)
        if match_evento:
            try:
                hora_evento_raw = match_evento.group(1)
            except IndexError:
                continue
            if hora_evento_raw is None:
                continue
            hora_formatada = normalizar_hora_capturada(hora_evento_raw)
            if not hora_formatada:
                continue

            try:
                dt_obj_inicial = datetime.strptime(
                    f"{data_log_contexto} {hora_formatada}", "%d/%m/%Y %H:%M"
                )
                dt_obj_final = _ajustar_data_evento_para_plantao(
                    dt_obj_inicial,
                    data_log_contexto,
                    inicio_plantao,
                    fim_plantao,
                    log_entry_datetime,
                )

                evento = {
                    "vtr": id_vtr_contexto or config.DEFAULT_VTR_ID,
                    "tipo": r_info["tipo"],
                    "hora_str": hora_formatada,
                    "data_str": dt_obj_final.strftime("%d/%m/%Y"),
                    "datetime_obj": dt_obj_final,
                    "linha_original": linha_original_str,
                }
                return [evento]
            except ValueError as ve:
                logger.error(
                    f"Erro de data/hora ao parsear evento: {ve}. Linha: '{linha_original_str}'"
                )
    return []


def extrair_eventos_de_bloco(
    bloco_linhas_orig: list,
    vtr_contexto_linha_prefixada: str,
    data_contexto_bloco: str,
    linha_original_referencia: str,
    log_entry_datetime_referencia: datetime = None,
    inicio_plantao: datetime = None,
    fim_plantao: datetime = None,
):
    eventos_acumulados_bloco = []
    for linha in bloco_linhas_orig:
        eventos = extrair_eventos_de_mensagem_simples(
            linha,
            data_contexto_bloco,
            vtr_contexto_linha_prefixada,
            linha_original_referencia,
            log_entry_datetime_referencia,
            inicio_plantao,
            fim_plantao,
        )
        if eventos:
            eventos_acumulados_bloco.extend(eventos)
    return eventos_acumulados_bloco
