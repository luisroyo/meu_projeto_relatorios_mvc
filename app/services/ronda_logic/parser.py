# parser.py
import logging
import re
from datetime import datetime, timedelta # Adicionar timedelta
from . import config
from .utils import normalizar_hora_capturada, normalizar_data_capturada
import unicodedata

logger = logging.getLogger(__name__)

def _limpar_e_normalizar_mensagem(texto: str) -> str:
    if not texto:
        return ""
    texto_normalizado = unicodedata.normalize('NFC', texto)
    texto_com_espacos_padronizados = re.sub(r'\s+', ' ', texto_normalizado)
    return texto_com_espacos_padronizados.strip()


def parse_linha_log_prefixo(linha_strip: str, ultima_vtr_conhecida_global: str):
    """
    Tenta parsear o prefixo padrão de uma linha de log.
    Retorna:
        - hora_linha_log_raw: Hora do log extraída do prefixo (string "HH:MM") ou None.
        - data_linha_original: Data extraída do prefixo da linha (DD/MM/YYYY) ou None.
        - id_vtr_para_eventos_desta_linha: VTR a ser usada para eventos extraídos da mensagem DESTA linha.
        - mensagem_eventos: A parte da mensagem da linha a ser escaneada para eventos.
        - vtr_contexto_geral_para_proximas_linhas: VTR que define o contexto para as linhas seguintes.
    """
    hora_linha_log_raw = None
    data_linha_original = None
    mensagem_eventos = linha_strip
    
    id_vtr_para_eventos_desta_linha = ultima_vtr_conhecida_global
    vtr_contexto_geral_para_proximas_linhas = ultima_vtr_conhecida_global

    match_prefixo = config.REGEX_PREFIXO_LINHA.match(linha_strip)
    if match_prefixo:
        hora_linha_log_raw_temp = match_prefixo.group(1) # Grupo 1: Hora do log
        data_str_raw = match_prefixo.group(2)          # Grupo 2: Data do log
        
        hora_linha_log_raw = normalizar_hora_capturada(hora_linha_log_raw_temp)
        if not hora_linha_log_raw:
             logger.warning(f"Falha ao normalizar hora do prefixo '{hora_linha_log_raw_temp}' na linha: {linha_strip}")

        data_linha_original = normalizar_data_capturada(data_str_raw)
        if not data_linha_original:
            logger.warning(f"Falha ao normalizar data do prefixo '{data_str_raw}' na linha: {linha_strip}")
            
        vtr_do_prefixo_str = match_prefixo.group(3)      # Grupo 3: VTR do prefixo
        mensagem_eventos = match_prefixo.group(4).strip() # Grupo 4: Mensagem

        vtr_do_prefixo_normalizada = None
        if vtr_do_prefixo_str:
            vtr_do_prefixo_normalizada = vtr_do_prefixo_str.upper().replace(" ", "")
            vtr_contexto_geral_para_proximas_linhas = vtr_do_prefixo_normalizada
            id_vtr_para_eventos_desta_linha = vtr_do_prefixo_normalizada
        
        match_vtr_na_mensagem = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(mensagem_eventos)
        if match_vtr_na_mensagem:
            vtr_especifica_da_mensagem = match_vtr_na_mensagem.group(1).upper().replace(" ", "")
            if id_vtr_para_eventos_desta_linha != vtr_especifica_da_mensagem:
                logger.info(f"VTR na mensagem ('{vtr_especifica_da_mensagem}') utilizada, sobrescrevendo contexto/prefixo VTR ('{id_vtr_para_eventos_desta_linha}') para eventos da linha: '{linha_strip[:80]}...'")
            id_vtr_para_eventos_desta_linha = vtr_especifica_da_mensagem
            mensagem_eventos = match_vtr_na_mensagem.group(2).strip()
            # VTR da mensagem se torna o contexto global se presente
            vtr_contexto_geral_para_proximas_linhas = id_vtr_para_eventos_desta_linha
        
        return hora_linha_log_raw, data_linha_original, id_vtr_para_eventos_desta_linha, _limpar_e_normalizar_mensagem(mensagem_eventos), vtr_contexto_geral_para_proximas_linhas
    else: 
        # Linha sem prefixo ou prefixo não مطابق: retorna Nones para hora/data do log
        return None, None, ultima_vtr_conhecida_global, _limpar_e_normalizar_mensagem(linha_strip), ultima_vtr_conhecida_global


def extrair_eventos_de_mensagem_simples(mensagem_raw: str, 
                                        data_log_contexto: str, 
                                        id_vtr_contexto: str, 
                                        linha_original_str: str,
                                        log_entry_datetime: datetime = None): # NOVO PARÂMETRO
    if not mensagem_raw:
        return []
        
    mensagem = _limpar_e_normalizar_mensagem(mensagem_raw)

    if not mensagem or not data_log_contexto or data_log_contexto == config.FALLBACK_DATA_INDEFINIDA:
        if data_log_contexto == config.FALLBACK_DATA_INDEFINIDA:
            logger.error(f"  Data do log INDEFINIDA para extrair evento da mensagem (original: '{mensagem_raw}'). Linha: '{linha_original_str}'.")
        return [] 

    for r_info in config.COMPILED_RONDA_EVENT_REGEXES:
        match_evento = r_info["regex"].search(mensagem)
        if match_evento:
            hora_evento_raw = None
            try:
                hora_evento_raw = match_evento.group(1)
            except IndexError:
                logger.error(f"  Regex '{r_info['regex'].pattern}' encontrou match em '{mensagem}' (original: '{mensagem_raw}') mas não tem grupo de captura para hora.")
                continue

            if hora_evento_raw is None:
                logger.warning(f"  Regex '{r_info['regex'].pattern}' encontrou match em '{mensagem}' (original: '{mensagem_raw}') mas grupo da hora é None.")
                continue

            hora_formatada = normalizar_hora_capturada(hora_evento_raw)
            if not hora_formatada:
                logger.warning(f"  Hora não pôde ser normalizada de '{hora_evento_raw}' na linha '{linha_original_str}' (original: '{mensagem_raw}'). Evento ignorado com esta regex.")
                continue
            
            # --- LÓGICA DE AJUSTE DE DATA (DIA ANTERIOR) ---
            data_para_evento_final_dt = None
            try:
                data_para_evento_final_dt = datetime.strptime(data_log_contexto, "%d/%m/%Y")
            except ValueError:
                logger.error(f"  Data de contexto inválida '{data_log_contexto}' ao tentar criar datetime para evento. Linha: {linha_original_str}")
                continue

            hora_evento_dt_obj = datetime.strptime(hora_formatada, "%H:%M").time()

            if log_entry_datetime and \
               log_entry_datetime.time().hour < 7 and \
               hora_evento_dt_obj.hour >= 18:
                logger.info(f"  Aplicando heurística de dia anterior para evento às {hora_formatada} (data do log: {data_log_contexto}, hora do log: {log_entry_datetime.strftime('%H:%M')}). Linha: {linha_original_str}")
                data_para_evento_final_dt -= timedelta(days=1)
            
            data_final_evento_str = data_para_evento_final_dt.strftime("%d/%m/%Y")
            dt_evento_str_completo = f"{data_final_evento_str} {hora_formatada}"
            # --- FIM DA LÓGICA DE AJUSTE DE DATA ---

            try:
                dt_obj = datetime.strptime(dt_evento_str_completo, "%d/%m/%Y %H:%M")
                evento = {
                    "vtr": id_vtr_contexto or config.DEFAULT_VTR_ID,
                    "tipo": r_info["tipo"],
                    "hora_str": hora_formatada,
                    "data_str": data_final_evento_str, # Usar a data possivelmente ajustada
                    "datetime_obj": dt_obj,
                    "linha_original": linha_original_str
                }
                logger.debug(f"    Evento simples encontrado por '{r_info['regex'].pattern}': VTR='{id_vtr_contexto}', Tipo='{r_info['tipo']}', Data='{data_final_evento_str}', Hora='{hora_formatada}' (Msg Original: '{mensagem_raw[:50]}...')")
                return [evento]
            except ValueError as ve:
                logger.error(f"  Erro de data/hora ao parsear evento '{linha_original_str}' com regex '{r_info['regex'].pattern}' (original: '{mensagem_raw}'): {ve}. Data Ctx: '{data_log_contexto}', Hora Fmt: '{hora_formatada}' (Raw: '{hora_evento_raw}'). Data Final Evento Tentada: {data_final_evento_str}")
    return []


def extrair_eventos_de_bloco(bloco_linhas_orig: list, 
                             vtr_contexto_linha_prefixada: str, 
                             data_contexto_bloco: str, 
                             linha_original_referencia: str,
                             log_entry_datetime_referencia: datetime = None): # NOVO PARÂMETRO
    eventos_acumulados_bloco = []
    data_bloco_especifica = data_contexto_bloco
    hora_inicio_raw_bloco = None
    hora_termino_raw_bloco = None
    vtr_para_eventos_deste_bloco = vtr_contexto_linha_prefixada

    bloco_linhas = list(bloco_linhas_orig)

    if bloco_linhas:
        primeira_linha_bloco_limpa = _limpar_e_normalizar_mensagem(bloco_linhas[0])
        match_vtr_na_primeira_linha_bloco = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(primeira_linha_bloco_limpa)
        if match_vtr_na_primeira_linha_bloco:
            vtr_detectada_no_bloco = match_vtr_na_primeira_linha_bloco.group(1).upper().replace(" ", "")
            if vtr_para_eventos_deste_bloco != vtr_detectada_no_bloco:
                 logger.info(f"VTR '{vtr_detectada_no_bloco}' na primeira linha do bloco (limpa: '{primeira_linha_bloco_limpa[:30]}...') usada, sobrescrevendo VTR de contexto da linha prefixada '{vtr_contexto_linha_prefixada}'.")
            vtr_para_eventos_deste_bloco = vtr_detectada_no_bloco
            bloco_linhas[0] = match_vtr_na_primeira_linha_bloco.group(2).strip()
        else:
            bloco_linhas[0] = primeira_linha_bloco_limpa


    linhas_processadas_indices = set()

    for idx, linha_b_raw in enumerate(bloco_linhas):
        linha_b_limpa = _limpar_e_normalizar_mensagem(linha_b_raw) if idx > 0 or not match_vtr_na_primeira_linha_bloco else linha_b_raw
        if not linha_b_limpa: continue

        match_data = config.REGEX_BLOCO_DATA.search(linha_b_limpa)
        if match_data:
            data_norm_bloco = normalizar_data_capturada(match_data.group(1))
            if data_norm_bloco: 
                data_bloco_especifica = data_norm_bloco # Data explícita no bloco ATUALIZA data_bloco_especifica
                logger.info(f"Data explícita '{data_bloco_especifica}' encontrada no bloco, sobrescrevendo data de contexto '{data_contexto_bloco}'. Linha: {linha_b_raw}")
            linhas_processadas_indices.add(idx); continue

        match_inicio = config.REGEX_BLOCO_INICIO.search(linha_b_limpa)
        if match_inicio:
            hora_inicio_raw_bloco = match_inicio.group(1)
            linhas_processadas_indices.add(idx); continue

        match_termino = config.REGEX_BLOCO_TERMINO.search(linha_b_limpa)
        if match_termino:
            hora_termino_raw_bloco = match_termino.group(1)
            linhas_processadas_indices.add(idx); continue
    
    for idx, linha_b_raw in enumerate(bloco_linhas):
        # A linha já foi limpa se era a primeira e teve VTR extraída, ou limpa no loop anterior.
        # Para extrair_eventos_de_mensagem_simples, passamos a raw, ela fará a limpeza.
        if idx in linhas_processadas_indices: continue
        linha_usada_para_evento = bloco_linhas[idx] # Usa a linha como está no buffer (pode já ter sido parcialmente processada)
        if not _limpar_e_normalizar_mensagem(linha_usada_para_evento): continue # Pula se a linha efetivamente ficar vazia
        
        if data_bloco_especifica and data_bloco_especifica != config.FALLBACK_DATA_INDEFINIDA:
            eventos_linha_bloco = extrair_eventos_de_mensagem_simples(
                linha_usada_para_evento, 
                data_bloco_especifica, 
                vtr_para_eventos_deste_bloco, 
                f"{linha_original_referencia} (bloco_linha_raw: {linha_b_raw[:30]})",
                log_entry_datetime_referencia # Passa o datetime da linha de log de referência
            )
            eventos_acumulados_bloco.extend(eventos_linha_bloco)
    
    # Processar Início e Término explícitos do bloco (com heurística de data)
    for tipo_evento_bloco, hora_raw_bloco in [("inicio", hora_inicio_raw_bloco), ("termino", hora_termino_raw_bloco)]:
        if hora_raw_bloco:
            hora_fmt = normalizar_hora_capturada(hora_raw_bloco)
            if hora_fmt and data_bloco_especifica and data_bloco_especifica != config.FALLBACK_DATA_INDEFINIDA:
                # --- LÓGICA DE AJUSTE DE DATA (DIA ANTERIOR) ---
                data_para_evento_final_dt_bloco = None
                try:
                    data_para_evento_final_dt_bloco = datetime.strptime(data_bloco_especifica, "%d/%m/%Y")
                except ValueError:
                    logger.error(f"  Data de bloco específica inválida '{data_bloco_especifica}' ao tentar criar datetime para evento explícito de bloco. Linha ref: {linha_original_referencia}")
                    continue
                
                hora_evento_dt_obj_bloco = datetime.strptime(hora_fmt, "%H:%M").time()

                if log_entry_datetime_referencia and \
                   log_entry_datetime_referencia.time().hour < 7 and \
                   hora_evento_dt_obj_bloco.hour >= 18:
                    logger.info(f"  Aplicando heurística de dia anterior para evento explícito de bloco ({tipo_evento_bloco} às {hora_fmt}, data do bloco: {data_bloco_especifica}, hora do log ref: {log_entry_datetime_referencia.strftime('%H:%M')}). Linha ref: {linha_original_referencia}")
                    data_para_evento_final_dt_bloco -= timedelta(days=1)
                
                data_final_evento_str_bloco = data_para_evento_final_dt_bloco.strftime("%d/%m/%Y")
                dt_evento_str_completo_bloco = f"{data_final_evento_str_bloco} {hora_fmt}"
                # --- FIM DA LÓGICA DE AJUSTE DE DATA ---
                try:
                    dt_obj = datetime.strptime(dt_evento_str_completo_bloco, "%d/%m/%Y %H:%M")
                    eventos_acumulados_bloco.append({
                        "vtr": vtr_para_eventos_deste_bloco or config.DEFAULT_VTR_ID, 
                        "tipo": tipo_evento_bloco, 
                        "hora_str": hora_fmt, 
                        "data_str": data_final_evento_str_bloco, # Usar a data possivelmente ajustada
                        "datetime_obj": dt_obj, 
                        "linha_original": f"{linha_original_referencia} (bloco_{tipo_evento_bloco}_explicito)"
                    })
                except ValueError as ve: 
                    logger.error(f"  Erro data/hora (bloco {tipo_evento_bloco} explícito) '{linha_original_referencia}': {ve}. Data Bloco: '{data_bloco_especifica}', Hora Fmt: '{hora_fmt}', Data Final Evento Tentada: {data_final_evento_str_bloco}")

    eventos_unicos_dict = {}
    for ev in eventos_acumulados_bloco:
        chave = (ev["vtr"], ev["tipo"], ev["data_str"], ev["hora_str"])
        if chave not in eventos_unicos_dict: 
            eventos_unicos_dict[chave] = ev
        else: 
            logger.debug(f"Evento duplicado dentro do bloco descartado: {ev} (chave: {chave})")
    
    return list(eventos_unicos_dict.values())