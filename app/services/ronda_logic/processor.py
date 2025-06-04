# processor.py
import logging
import re
from datetime import datetime, timedelta
from . import config
from .parser import parse_linha_log_prefixo, extrair_eventos_de_mensagem_simples, extrair_eventos_de_bloco
from .processing import parear_eventos_ronda
from .report import formatar_relatorio_rondas
from .utils import normalizar_data_capturada # Para data do plantão manual

logger = logging.getLogger(__name__)

def calcular_intervalo_plantao(data_plantao_str: str, escala_plantao_str: str):
    """
    Calcula o datetime de início e fim do plantão.
    Retorna (datetime_inicio, datetime_fim, data_para_cabecalho_valida).
    data_plantao_str é a data principal (ex: dia em que termina o noturno, ou dia do diurno).
    escala_plantao_str é "HH-MM" (ex: "06-18" ou "18-06") ou "HHh às MMh".
    """
    if not data_plantao_str or not escala_plantao_str:
        return None, None, config.FALLBACK_DATA_INDEFINIDA

    data_base_dt = None
    data_cabecalho = config.FALLBACK_DATA_INDEFINIDA
    try:
        data_norm = normalizar_data_capturada(data_plantao_str)
        if not data_norm or len(data_norm.split('/')[2]) != 4 : 
             raise ValueError("Data normalizada inválida ou ano não tem 4 dígitos")
        data_base_dt = datetime.strptime(data_norm, "%d/%m/%Y")
        data_cabecalho = data_norm
    except ValueError as e:
        logger.error(f"Data de plantão manual ('{data_plantao_str}') inválida: {e}. Não é possível calcular intervalo.")
        return None, None, data_plantao_str 

    escala_normalizada_para_parse = escala_plantao_str.strip()
    match_escala_humanizada = re.match(r"(\d{1,2})h\s*às\s*(\d{1,2})h", escala_normalizada_para_parse, re.IGNORECASE)
    if match_escala_humanizada:
        escala_normalizada_para_parse = f"{match_escala_humanizada.group(1)}-{match_escala_humanizada.group(2)}"
        logger.info(f"Escala '{escala_plantao_str}' normalizada para '{escala_normalizada_para_parse}' para processamento.")

    partes_escala = escala_normalizada_para_parse.split('-')
    if len(partes_escala) != 2:
        logger.error(f"Escala de plantão ('{escala_plantao_str}' -> tentativa como '{escala_normalizada_para_parse}') inválida. Use formato HH-MM ou HHh às MMh.")
        return None, None, data_cabecalho

    try:
        hora_inicio_escala = int(partes_escala[0])
        hora_fim_escala = int(partes_escala[1]) 
    except ValueError:
        logger.error(f"Horas da escala ('{escala_normalizada_para_parse}') não são numéricas.")
        return None, None, data_cabecalho

    if not (0 <= hora_inicio_escala <= 23 and 0 <= hora_fim_escala <= 23):
        logger.error(f"Horas da escala ('{hora_inicio_escala}', '{hora_fim_escala}') estão fora do intervalo válido (0-23).")
        return None, None, data_cabecalho

    if hora_inicio_escala < hora_fim_escala: # Plantão Diurno (ex: 06-18)
        inicio_plantao = data_base_dt.replace(hour=hora_inicio_escala, minute=0, second=0, microsecond=0)
        fim_plantao = data_base_dt.replace(hour=hora_fim_escala, minute=0, second=0, microsecond=0)
    else: # Plantão Noturno (ex: 18-06, cruza meia-noite)
        inicio_plantao_dia_anterior = data_base_dt - timedelta(days=1)
        inicio_plantao = inicio_plantao_dia_anterior.replace(hour=hora_inicio_escala, minute=0, second=0, microsecond=0)
        fim_plantao = data_base_dt.replace(hour=hora_fim_escala, minute=0, second=0, microsecond=0)
        
    logger.info(f"Intervalo de plantão calculado: de {inicio_plantao.strftime('%d/%m/%Y %H:%M')} a {fim_plantao.strftime('%d/%m/%Y %H:%M')}")
    return inicio_plantao, fim_plantao, data_cabecalho


def processar_log_de_rondas(log_bruto_rondas_str: str,
                            nome_condominio_str: str,
                            data_plantao_manual_str: str = None, 
                            escala_plantao_str: str = None): 
    
    logger.info(f"Processando log para: {nome_condominio_str}, Data Plantão: {data_plantao_manual_str}, Escala: {escala_plantao_str}")
    if not log_bruto_rondas_str or not log_bruto_rondas_str.strip():
        logger.warning("Log de ronda bruto está vazio.")
        return "Nenhum log de ronda fornecido ou log vazio."

    inicio_intervalo_plantao, fim_intervalo_plantao, data_formatada_cabecalho = calcular_intervalo_plantao(data_plantao_manual_str, escala_plantao_str)

    if not inicio_intervalo_plantao or not fim_intervalo_plantao:
        logger.error("Não foi possível determinar o intervalo do plantão devido a data ou escala inválida. Processando sem filtro de data/hora do plantão.")
        # O relatório usará data_formatada_cabecalho, que pode ser o fallback ou a data original problemática.

    log_processado = log_bruto_rondas_str.replace('\\[', '[').replace('\\]', ']')
    linhas = log_processado.strip().split('\n')
    
    eventos_encontrados_todos = []
    
    # Contexto global que é carregado entre linhas com prefixo
    ultima_vtr_identificada_global = config.DEFAULT_VTR_ID
    ultima_data_valida_global = config.FALLBACK_DATA_INDEFINIDA

    # Buffer para linhas de bloco e seu contexto específico
    buffer_bloco_atual = []
    vtr_para_contexto_bloco_atual = ultima_vtr_identificada_global 
    data_para_contexto_bloco_atual = ultima_data_valida_global
    linha_referencia_para_bloco_atual = ""


    def processar_buffer_bloco_se_existente(buffer, vtr_ctx_bloco, data_ctx_bloco, ref_linha_bloco, lista_eventos_destino):
        if buffer:
            logger.debug(f"Processando buffer de bloco com {len(buffer)} linhas. Contexto VTR: '{vtr_ctx_bloco}', Data: '{data_ctx_bloco}'. Linha Ref: '{ref_linha_bloco[:50]}...'")
            eventos_do_bloco = extrair_eventos_de_bloco(buffer, vtr_ctx_bloco, data_ctx_bloco, ref_linha_bloco)
            if eventos_do_bloco:
                lista_eventos_destino.extend(eventos_do_bloco)
                logger.debug(f"  Eventos extraídos do bloco: {eventos_do_bloco}")
            buffer.clear()

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip:
            continue

        logger.debug(f"Processando linha {i+1}: '{linha_strip[:100]}...' (Contexto VTR Global: {ultima_vtr_identificada_global})")

        data_da_linha_com_prefixo, vtr_para_eventos_desta_linha, msg_da_linha_com_prefixo, vtr_global_atualizada = \
            parse_linha_log_prefixo(linha_strip, ultima_vtr_identificada_global)
        
        if data_da_linha_com_prefixo: 
            # Esta linha tem um prefixo de data, é uma entrada principal.
            # Primeiro, processa qualquer bloco anterior que estava pendente.
            processar_buffer_bloco_se_existente(
                buffer_bloco_atual, 
                vtr_para_contexto_bloco_atual, # Usa o contexto do bloco que estava sendo formado
                data_para_contexto_bloco_atual, 
                linha_referencia_para_bloco_atual, 
                eventos_encontrados_todos
            )
            
            # Atualiza o contexto global para as próximas iterações
            ultima_vtr_identificada_global = vtr_global_atualizada
            if data_da_linha_com_prefixo != config.FALLBACK_DATA_INDEFINIDA and data_da_linha_com_prefixo : # Garante que é uma data válida
                 ultima_data_valida_global = data_da_linha_com_prefixo
            
            # Define o contexto para o PRÓXIMO bloco que esta linha pode iniciar
            vtr_para_contexto_bloco_atual = vtr_para_eventos_desta_linha # A VTR mais específica desta linha contextualiza o bloco seguinte
            data_para_contexto_bloco_atual = ultima_data_valida_global # A data desta linha contextualiza o bloco seguinte
            linha_referencia_para_bloco_atual = linha_original

            # Se houver mensagem nesta linha com prefixo, tenta extrair eventos dela
            if msg_da_linha_com_prefixo:
                logger.debug(f"  Linha com prefixo. VTR para msg: '{vtr_para_eventos_desta_linha}', Data: '{ultima_data_valida_global}', Msg: '{msg_da_linha_com_prefixo[:50]}...'")
                eventos_msg_simples = extrair_eventos_de_mensagem_simples(
                    msg_da_linha_com_prefixo, 
                    ultima_data_valida_global, # Usa a data da linha atual
                    vtr_para_eventos_desta_linha, # Usa a VTR específica para esta mensagem
                    linha_original
                )
                if eventos_msg_simples:
                    eventos_encontrados_todos.extend(eventos_msg_simples)
                    logger.debug(f"  Eventos de msg simples (linha com prefixo): {eventos_msg_simples}")
        
        else: 
            # Linha sem prefixo de data: é parte de um bloco de continuação.
            # A 'msg_da_linha_com_prefixo' aqui é a linha_strip inteira.
            # 'vtr_para_eventos_desta_linha' e 'vtr_global_atualizada' são o 'ultima_vtr_identificada_global' anterior.
            
            # Heurística: Se um bloco QRA aparece e não estávamos construindo um bloco,
            # ele ainda usa o contexto da última linha com prefixo.
            if not buffer_bloco_atual and config.REGEX_BLOCO_QRA.match(msg_da_linha_com_prefixo):
                logger.debug(f"  Linha QRA detectada '{msg_da_linha_com_prefixo[:50]}...' iniciando novo bloco (ou continuando contexto).")
                # Se havia um bloco anterior (improvável aqui, mas por segurança), processa-o.
                # processar_buffer_bloco_se_existente(...) # Normalmente o buffer estaria vazio.
                # A linha_referencia_para_bloco_atual já deve ter sido definida pela última linha com prefixo.
                # Se esta é a PRIMEIRA linha do log e é um QRA, linha_referencia_para_bloco_atual será vazia.
                if not linha_referencia_para_bloco_atual:
                    linha_referencia_para_bloco_atual = linha_original


            buffer_bloco_atual.append(msg_da_linha_com_prefixo)
            logger.debug(f"  Adicionando linha ao buffer do bloco: '{msg_da_linha_com_prefixo[:50]}...'. Buffer com {len(buffer_bloco_atual)} linhas.")

    # Processa qualquer bloco restante no final do log
    processar_buffer_bloco_se_existente(
        buffer_bloco_atual, 
        vtr_para_contexto_bloco_atual, 
        data_para_contexto_bloco_atual, 
        linha_referencia_para_bloco_atual, 
        eventos_encontrados_todos
    )

    eventos_do_plantao = []
    if inicio_intervalo_plantao and fim_intervalo_plantao:
        for ev in eventos_encontrados_todos:
            if ev.get("datetime_obj"):
                if inicio_intervalo_plantao <= ev["datetime_obj"] < fim_intervalo_plantao:
                    eventos_do_plantao.append(ev)
                else:
                    logger.debug(f"Evento FORA do intervalo do plantão: {ev['datetime_obj']} (VTR: {ev['vtr']}, Tipo: {ev['tipo']})")
            else: 
                logger.warning(f"Evento sem datetime_obj não pode ser filtrado por data: {ev.get('linha_original', 'N/A')}")
    else: 
        logger.warning("Intervalo do plantão não definido ou inválido. Incluindo todos os eventos parseados que possuem datetime_obj.")
        eventos_do_plantao = [ev for ev in eventos_encontrados_todos if ev.get("datetime_obj")]


    if not eventos_do_plantao:
        msg_retorno = "Nenhum evento de ronda (início/término com data/hora reconhecível) foi identificado no log fornecido"
        if inicio_intervalo_plantao and fim_intervalo_plantao: # Se o intervalo FOI definido mas nada caiu nele
            msg_retorno += f" para o plantão de {inicio_intervalo_plantao.strftime('%d/%m/%Y %H:%M')} a {fim_intervalo_plantao.strftime('%d/%m/%Y %H:%M')}."
        elif not data_plantao_manual_str or not escala_plantao_str : # Se o intervalo não foi definido por falta de input
             msg_retorno += " (data/escala do plantão não fornecida para filtragem)."
        else: # Se o intervalo não foi definido por input inválido
            msg_retorno += f" (problema ao definir intervalo para data '{data_plantao_manual_str}' e escala '{escala_plantao_str}', portanto, nenhum evento pôde ser associado a um plantão válido)."
        logger.info(msg_retorno)
        return msg_retorno

    eventos_do_plantao.sort(key=lambda x: x["datetime_obj"])
    logger.info(f"Total de {len(eventos_do_plantao)} eventos encontrados DENTRO do intervalo do plantão (ou todos, se sem filtro).")

    rondas_pareadas, alertas_pareamento = parear_eventos_ronda(eventos_do_plantao)

    if not rondas_pareadas and not alertas_pareamento and eventos_do_plantao:
        return "Eventos de ronda identificados, mas insuficientes para formar pares de início/término ou gerar alertas significativos no período do plantão."
    elif not rondas_pareadas and not alertas_pareamento and not eventos_do_plantao: 
        return "Nenhum evento de ronda válido identificado no período do plantão."


    relatorio_final = formatar_relatorio_rondas(
        nome_condominio_str,
        data_formatada_cabecalho, 
        escala_plantao_str, 
        eventos_do_plantao, 
        rondas_pareadas,
        alertas_pareamento
    )

    rondas_completas_count = sum(1 for r in rondas_pareadas if r.get("inicio_dt") and r.get("termino_dt"))
    logger.info(f"Relatório para {nome_condominio_str} formatado. {len(eventos_do_plantao)} eventos no plantão, {rondas_completas_count} rondas completas, {len(alertas_pareamento)} alertas.")
    return relatorio_final