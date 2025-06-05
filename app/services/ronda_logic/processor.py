# processor.py
import logging
import re
from datetime import datetime, timedelta
from . import config
from .parser import parse_linha_log_prefixo, extrair_eventos_de_mensagem_simples, extrair_eventos_de_bloco
from .processing import parear_eventos_ronda
from .report import formatar_relatorio_rondas
from .utils import normalizar_data_capturada, normalizar_hora_capturada # Adicionar normalizar_hora_capturada se não estiver

logger = logging.getLogger(__name__)

# ... (função calcular_intervalo_plantao permanece a mesma) ...
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
        # Para plantão noturno, data_base_dt é o dia em que o plantão TERMINA
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

    log_processado = log_bruto_rondas_str.replace('\\[', '[').replace('\\]', ']')
    linhas = log_processado.strip().split('\n')
    
    eventos_encontrados_todos = []
    
    ultima_vtr_identificada_global = config.DEFAULT_VTR_ID
    ultima_data_valida_global = config.FALLBACK_DATA_INDEFINIDA
    ultimo_datetime_log_global = None # Para heurística de data

    buffer_bloco_atual = []
    vtr_para_contexto_bloco_atual = ultima_vtr_identificada_global 
    data_para_contexto_bloco_atual = ultima_data_valida_global
    linha_referencia_para_bloco_atual = ""
    datetime_log_referencia_para_bloco_atual = None


    def processar_buffer_bloco_se_existente(buffer, vtr_ctx_bloco, data_ctx_bloco, ref_linha_bloco, ref_datetime_log_bloco, lista_eventos_destino):
        if buffer:
            logger.debug(f"Processando buffer de bloco com {len(buffer)} linhas. Contexto VTR: '{vtr_ctx_bloco}', Data: '{data_ctx_bloco}'. Linha Ref: '{ref_linha_bloco[:50]}...'")
            eventos_do_bloco = extrair_eventos_de_bloco(buffer, vtr_ctx_bloco, data_ctx_bloco, ref_linha_bloco, ref_datetime_log_bloco)
            if eventos_do_bloco:
                lista_eventos_destino.extend(eventos_do_bloco)
                logger.debug(f"  Eventos extraídos do bloco: {eventos_do_bloco}")
            buffer.clear()

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip:
            continue

        logger.debug(f"Processando linha {i+1}: '{linha_strip[:100]}...' (Contexto VTR Global: {ultima_vtr_identificada_global}, Data Global: {ultima_data_valida_global})")

        # hora_log_desta_linha é a HORA da entrada do log (ex: "22:08" de "[22:08, ...]")
        hora_log_desta_linha_raw, data_da_linha_com_prefixo, vtr_para_eventos_desta_linha, msg_da_linha_com_prefixo, vtr_global_atualizada = \
            parse_linha_log_prefixo(linha_strip, ultima_vtr_identificada_global)
        
        current_log_entry_datetime = None
        if data_da_linha_com_prefixo and data_da_linha_com_prefixo != config.FALLBACK_DATA_INDEFINIDA and hora_log_desta_linha_raw:
            try:
                current_log_entry_datetime = datetime.strptime(f"{data_da_linha_com_prefixo} {hora_log_desta_linha_raw}", "%d/%m/%Y %H:%M")
                ultimo_datetime_log_global = current_log_entry_datetime # Atualiza o datetime global do log
            except ValueError:
                logger.warning(f"Não foi possível criar datetime da entrada de log: data='{data_da_linha_com_prefixo}', hora='{hora_log_desta_linha_raw}'")
        elif data_da_linha_com_prefixo and data_da_linha_com_prefixo != config.FALLBACK_DATA_INDEFINIDA and not hora_log_desta_linha_raw:
             # Se temos data mas não hora do log (improvável com a nova regex, mas seguro)
             # Tentamos usar o ultimo_datetime_log_global se a data for a mesma, ou criamos um com hora 00:00
            if ultima_data_valida_global == data_da_linha_com_prefixo and ultimo_datetime_log_global:
                 current_log_entry_datetime = ultimo_datetime_log_global # Reusa o último se a data não mudou
            else:
                try:
                    current_log_entry_datetime = datetime.strptime(data_da_linha_com_prefixo, "%d/%m/%Y") # Default to 00:00
                except ValueError: pass # Mantém None
        else: # Linha sem prefixo de data/hora, usa o contexto de datetime de log global
            current_log_entry_datetime = ultimo_datetime_log_global


        if data_da_linha_com_prefixo: 
            processar_buffer_bloco_se_existente(
                buffer_bloco_atual, 
                vtr_para_contexto_bloco_atual,
                data_para_contexto_bloco_atual, 
                linha_referencia_para_bloco_atual,
                datetime_log_referencia_para_bloco_atual, # Passa o datetime do log de referência do bloco
                eventos_encontrados_todos
            )
            
            ultima_vtr_identificada_global = vtr_global_atualizada
            if data_da_linha_com_prefixo != config.FALLBACK_DATA_INDEFINIDA and data_da_linha_com_prefixo:
                 ultima_data_valida_global = data_da_linha_com_prefixo
            
            vtr_para_contexto_bloco_atual = vtr_para_eventos_desta_linha
            data_para_contexto_bloco_atual = ultima_data_valida_global
            linha_referencia_para_bloco_atual = linha_original
            datetime_log_referencia_para_bloco_atual = current_log_entry_datetime # Define para o próximo bloco

            if msg_da_linha_com_prefixo:
                logger.debug(f"  Linha com prefixo. VTR para msg: '{vtr_para_eventos_desta_linha}', Data Ctx: '{ultima_data_valida_global}', Msg: '{msg_da_linha_com_prefixo[:50]}...', Log Entry DT: {current_log_entry_datetime}")
                eventos_msg_simples = extrair_eventos_de_mensagem_simples(
                    msg_da_linha_com_prefixo, 
                    ultima_data_valida_global,
                    vtr_para_eventos_desta_linha,
                    linha_original,
                    current_log_entry_datetime # Passa o datetime da entrada de log atual
                )
                if eventos_msg_simples:
                    eventos_encontrados_todos.extend(eventos_msg_simples)
        
        else: 
            # Linha sem prefixo de data: parte de um bloco. msg_da_linha_com_prefixo é a linha inteira.
            if not buffer_bloco_atual and config.REGEX_BLOCO_QRA.match(msg_da_linha_com_prefixo):
                logger.debug(f"  Linha QRA detectada '{msg_da_linha_com_prefixo[:50]}...' iniciando novo bloco (ou continuando contexto).")
                if not linha_referencia_para_bloco_atual: # Se é a primeira linha do log e é um QRA
                    linha_referencia_para_bloco_atual = linha_original
                    datetime_log_referencia_para_bloco_atual = ultimo_datetime_log_global # Usa o último conhecido

            buffer_bloco_atual.append(msg_da_linha_com_prefixo) # Adiciona a mensagem (linha inteira)
            logger.debug(f"  Adicionando linha ao buffer do bloco: '{msg_da_linha_com_prefixo[:50]}...'. Buffer com {len(buffer_bloco_atual)} linhas.")

    processar_buffer_bloco_se_existente(
        buffer_bloco_atual, 
        vtr_para_contexto_bloco_atual, 
        data_para_contexto_bloco_atual, 
        linha_referencia_para_bloco_atual,
        datetime_log_referencia_para_bloco_atual, # Passa o datetime do log de referência do último bloco
        eventos_encontrados_todos
    )

    eventos_do_plantao = []
    if inicio_intervalo_plantao and fim_intervalo_plantao:
        for ev in eventos_encontrados_todos:
            if ev.get("datetime_obj"):
                # Adiciona uma pequena tolerância no fim_intervalo_plantao para incluir eventos que terminam exatamente na hora de fim
                if inicio_intervalo_plantao <= ev["datetime_obj"] < (fim_intervalo_plantao + timedelta(seconds=1)):
                    eventos_do_plantao.append(ev)
                else:
                    logger.debug(f"Evento FORA do intervalo do plantão: {ev['datetime_obj']} (VTR: {ev['vtr']}, Tipo: {ev['tipo']})")
            else: 
                logger.warning(f"Evento sem datetime_obj não pode ser filtrado por data: {ev.get('linha_original', 'N/A')}")
    else: 
        logger.warning("Intervalo do plantão não definido ou inválido. Incluindo todos os eventos parseados que possuem datetime_obj.")
        eventos_do_plantao = [ev for ev in eventos_encontrados_todos if ev.get("datetime_obj")]


    if not eventos_do_plantao:
        # ... (lógica de mensagem de retorno existente) ...
        msg_retorno = "Nenhum evento de ronda (início/término com data/hora reconhecível) foi identificado no log fornecido"
        if inicio_intervalo_plantao and fim_intervalo_plantao:
            msg_retorno += f" para o plantão de {inicio_intervalo_plantao.strftime('%d/%m/%Y %H:%M')} a {fim_intervalo_plantao.strftime('%d/%m/%Y %H:%M')}."
        elif not data_plantao_manual_str or not escala_plantao_str :
             msg_retorno += " (data/escala do plantão não fornecida para filtragem)."
        else:
            msg_retorno += f" (problema ao definir intervalo para data '{data_plantao_manual_str}' e escala '{escala_plantao_str}', portanto, nenhum evento pôde ser associado a um plantão válido)."
        logger.info(msg_retorno)
        return msg_retorno


    eventos_do_plantao.sort(key=lambda x: x["datetime_obj"])
    logger.info(f"Total de {len(eventos_do_plantao)} eventos encontrados DENTRO do intervalo do plantão (ou todos, se sem filtro).")

    rondas_pareadas, alertas_pareamento = parear_eventos_ronda(eventos_do_plantao)

    # ... (lógica de retorno e formatação de relatório existente) ...
    if not rondas_pareadas and not alertas_pareamento and eventos_do_plantao:
        # Se há eventos mas não formaram rondas nem alertas, pode ser útil informar.
        # Ex: muitos inícios sem términos, ou vice-versa, mas não o suficiente para alertas específicos do pareador.
        return "Eventos de ronda identificados, mas insuficientes para formar pares de início/término ou gerar alertas significativos no período do plantão."
    elif not rondas_pareadas and not alertas_pareamento and not eventos_do_plantao: 
        # Este caso já é coberto pelo "Nenhum evento de ronda..." acima.
        # Mas, para maior clareza se chegar aqui após o filtro de plantão:
        return "Nenhum evento de ronda válido identificado no período do plantão."


    relatorio_final = formatar_relatorio_rondas(
        nome_condominio_str,
        data_formatada_cabecalho, 
        escala_plantao_str, 
        eventos_do_plantao, # Passar os eventos filtrados (ou todos se sem filtro)
        rondas_pareadas,
        alertas_pareamento
    )

    rondas_completas_count = sum(1 for r in rondas_pareadas if r.get("inicio_dt") and r.get("termino_dt"))
    logger.info(f"Relatório para {nome_condominio_str} formatado. {len(eventos_do_plantao)} eventos no plantão, {rondas_completas_count} rondas completas, {len(alertas_pareamento)} alertas.")
    return relatorio_final