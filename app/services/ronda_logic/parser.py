# parser.py
import logging
import re # Adicionar se não estiver já importado no topo de parser.py
from datetime import datetime
from . import config 
from .utils import normalizar_hora_capturada, normalizar_data_capturada
import unicodedata # <--- ADICIONAR IMPORTAÇÃO

logger = logging.getLogger(__name__)

# Função auxiliar para limpar e normalizar mensagens
def _limpar_e_normalizar_mensagem(texto: str) -> str:
    if not texto:
        return ""
    texto_normalizado = unicodedata.normalize('NFC', texto)
    # Talvez o re.sub abaixo seja o problema? Tente comentar temporariamente para testar.
    # Se comentar, certifique-se de que as regexes em config.py são robustas a múltiplos espaços
    # usando \s* ou \s+ onde apropriado, em vez de espaços literais.
    texto_com_espacos_padronizados = re.sub(r'\s+', ' ', texto_normalizado) 
    return texto_com_espacos_padronizados.strip()


# Manter parse_linha_log_prefixo como na ÚLTIMA resposta que corrigiu a lógica de VTR.
# A modificação abaixo é em extrair_eventos_de_mensagem_simples e, por consequência, em como
# extrair_eventos_de_bloco chama ela.

def parse_linha_log_prefixo(linha_strip: str, ultima_vtr_conhecida_global: str):
    """
    Tenta parsear o prefixo padrão de uma linha de log.
    Retorna:
        - data_linha_original: Data extraída do prefixo da linha (DD/MM/YYYY) ou None.
        - id_vtr_para_eventos_desta_linha: VTR a ser usada para eventos extraídos da mensagem DESTA linha.
                                          Prioriza VTR na mensagem, depois VTR no prefixo, depois global.
        - mensagem_eventos: A parte da mensagem da linha a ser escaneada para eventos.
        - vtr_contexto_geral_para_proximas_linhas: VTR que define o contexto para as linhas seguintes
                                                  (geralmente da VTR do prefixo, ou da mensagem se não houver no prefixo).
    """
    data_linha_original = None
    mensagem_eventos = linha_strip 
    
    id_vtr_para_eventos_desta_linha = ultima_vtr_conhecida_global
    vtr_contexto_geral_para_proximas_linhas = ultima_vtr_conhecida_global

    match_prefixo = config.REGEX_PREFIXO_LINHA.match(linha_strip)
    if match_prefixo:
        data_str_raw = match_prefixo.group(1)
        data_linha_original = normalizar_data_capturada(data_str_raw)
        if not data_linha_original:
            logger.warning(f"Falha ao normalizar data do prefixo '{data_str_raw}' na linha: {linha_strip}")
            
        vtr_do_prefixo_str = match_prefixo.group(2) 
        mensagem_eventos = match_prefixo.group(3).strip() # Strip inicial aqui

        vtr_do_prefixo_normalizada = None
        if vtr_do_prefixo_str:
            vtr_do_prefixo_normalizada = vtr_do_prefixo_str.upper().replace(" ", "")
            vtr_contexto_geral_para_proximas_linhas = vtr_do_prefixo_normalizada
            id_vtr_para_eventos_desta_linha = vtr_do_prefixo_normalizada
        
        match_vtr_na_mensagem = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(mensagem_eventos) # Match na mensagem já stripada
        if match_vtr_na_mensagem:
            vtr_especifica_da_mensagem = match_vtr_na_mensagem.group(1).upper().replace(" ", "")
            if id_vtr_para_eventos_desta_linha != vtr_especifica_da_mensagem:
                logger.info(f"VTR na mensagem ('{vtr_especifica_da_mensagem}') utilizada, sobrescrevendo contexto/prefixo VTR ('{id_vtr_para_eventos_desta_linha}') para eventos da linha: '{linha_strip[:80]}...'")
            id_vtr_para_eventos_desta_linha = vtr_especifica_da_mensagem
            mensagem_eventos = match_vtr_na_mensagem.group(2).strip() 
            if not vtr_do_prefixo_normalizada:
                 vtr_contexto_geral_para_proximas_linhas = id_vtr_para_eventos_desta_linha
        
        return data_linha_original, id_vtr_para_eventos_desta_linha, _limpar_e_normalizar_mensagem(mensagem_eventos), vtr_contexto_geral_para_proximas_linhas
    else: 
        return None, ultima_vtr_conhecida_global, _limpar_e_normalizar_mensagem(linha_strip), ultima_vtr_conhecida_global


def extrair_eventos_de_mensagem_simples(mensagem_raw: str, data_log_contexto: str, id_vtr_contexto: str, linha_original_str: str):
    if not mensagem_raw: # Se a mensagem original já for vazia, não há o que fazer
        return []
        
    mensagem = _limpar_e_normalizar_mensagem(mensagem_raw) # Limpa e normaliza aqui!

    if not mensagem or not data_log_contexto or data_log_contexto == config.FALLBACK_DATA_INDEFINIDA:
        if data_log_contexto == config.FALLBACK_DATA_INDEFINIDA:
            logger.error(f"  Data do log INDEFINIDA para extrair evento da mensagem (original: '{mensagem_raw}'). Linha: '{linha_original_str}'.")
        return [] 

    for r_info in config.COMPILED_RONDA_EVENT_REGEXES:
        # Usa a mensagem normalizada para o search
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
            
            dt_evento_str = f"{data_log_contexto} {hora_formatada}"
            try:
                dt_obj = datetime.strptime(dt_evento_str, "%d/%m/%Y %H:%M")
                evento = {
                    "vtr": id_vtr_contexto or config.DEFAULT_VTR_ID,
                    "tipo": r_info["tipo"],
                    "hora_str": hora_formatada,
                    "data_str": data_log_contexto,
                    "datetime_obj": dt_obj,
                    "linha_original": linha_original_str 
                }
                logger.debug(f"    Evento simples encontrado por '{r_info['regex'].pattern}': VTR='{id_vtr_contexto}', Tipo='{r_info['tipo']}', Hora='{hora_formatada}' (Msg Original: '{mensagem_raw[:50]}...')")
                return [evento] 
            except ValueError as ve:
                logger.error(f"  Erro de data/hora ao parsear evento '{linha_original_str}' com regex '{r_info['regex'].pattern}' (original: '{mensagem_raw}'): {ve}. Data: '{data_log_contexto}', Hora Fmt: '{hora_formatada}' (Raw: '{hora_evento_raw}').")
    return []


def extrair_eventos_de_bloco(bloco_linhas_orig: list, vtr_contexto_linha_prefixada: str, data_contexto_bloco: str, linha_original_referencia: str):
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
            # Atualiza a linha no buffer (já limpa) para remover a VTR
            bloco_linhas[0] = match_vtr_na_primeira_linha_bloco.group(2).strip() # O strip aqui é no resto da msg já limpa
        else:
            # Se não achou VTR, a primeira linha ainda precisa ser limpa para o processamento seguinte
            bloco_linhas[0] = primeira_linha_bloco_limpa


    linhas_processadas_indices = set() 

    for idx, linha_b_raw in enumerate(bloco_linhas):
        # Limpa cada linha do bloco ANTES de tentar extrair Data, Início, Término explícito
        linha_b_limpa = _limpar_e_normalizar_mensagem(linha_b_raw) if idx > 0 or not match_vtr_na_primeira_linha_bloco else linha_b_raw # Se idx==0 e VTR foi removida, linha_b_raw já é o resto limpo
        if not linha_b_limpa: continue

        match_data = config.REGEX_BLOCO_DATA.search(linha_b_limpa)
        if match_data:
            data_norm = normalizar_data_capturada(match_data.group(1))
            if data_norm: data_bloco_especifica = data_norm
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
        linha_b_limpa_para_evento = _limpar_e_normalizar_mensagem(linha_b_raw) if idx > 0 or not match_vtr_na_primeira_linha_bloco else linha_b_raw
        if not linha_b_limpa_para_evento or idx in linhas_processadas_indices: continue
        
        if data_bloco_especifica and data_bloco_especifica != config.FALLBACK_DATA_INDEFINIDA:
            # Passa a linha original raw para extrair_eventos_de_mensagem_simples, pois ela fará sua própria limpeza
            eventos_linha_bloco = extrair_eventos_de_mensagem_simples(
                linha_b_raw, # Passa a linha como veio do buffer, a função interna limpará
                data_bloco_especifica, 
                vtr_para_eventos_deste_bloco, 
                f"{linha_original_referencia} (bloco_linha_raw: {linha_b_raw[:30]})"
            )
            eventos_acumulados_bloco.extend(eventos_linha_bloco)
    
    if hora_inicio_raw_bloco: # ... (lógica de criação de evento explícito como antes) ...
        hora_fmt = normalizar_hora_capturada(hora_inicio_raw_bloco)
        if hora_fmt and data_bloco_especifica and data_bloco_especifica != config.FALLBACK_DATA_INDEFINIDA:
            try:
                dt_obj = datetime.strptime(f"{data_bloco_especifica} {hora_fmt}", "%d/%m/%Y %H:%M")
                eventos_acumulados_bloco.append({
                    "vtr": vtr_para_eventos_deste_bloco or config.DEFAULT_VTR_ID, "tipo": "inicio", 
                    "hora_str": hora_fmt, "data_str": data_bloco_especifica, 
                    "datetime_obj": dt_obj, "linha_original": f"{linha_original_referencia} (bloco_inicio_explicito)"
                })
            except ValueError as ve: logger.error(f"  Erro data/hora (bloco início explícito) '{linha_original_referencia}': {ve}.")

    if hora_termino_raw_bloco: # ... (lógica de criação de evento explícito como antes) ...
        hora_fmt = normalizar_hora_capturada(hora_termino_raw_bloco)
        if hora_fmt and data_bloco_especifica and data_bloco_especifica != config.FALLBACK_DATA_INDEFINIDA:
            try:
                dt_obj = datetime.strptime(f"{data_bloco_especifica} {hora_fmt}", "%d/%m/%Y %H:%M")
                eventos_acumulados_bloco.append({
                    "vtr": vtr_para_eventos_deste_bloco or config.DEFAULT_VTR_ID, "tipo": "termino", 
                    "hora_str": hora_fmt, "data_str": data_bloco_especifica, 
                    "datetime_obj": dt_obj, "linha_original": f"{linha_original_referencia} (bloco_termino_explicito)"
                })
            except ValueError as ve: logger.error(f"  Erro data/hora (bloco término explícito) '{linha_original_referencia}': {ve}.")

    eventos_unicos_dict = {}
    for ev in eventos_acumulados_bloco:
        chave = (ev["vtr"], ev["tipo"], ev["data_str"], ev["hora_str"])
        if chave not in eventos_unicos_dict: eventos_unicos_dict[chave] = ev
        else: logger.debug(f"Evento duplicado dentro do bloco descartado: {ev} (chave: {chave})")
    
    return list(eventos_unicos_dict.values())