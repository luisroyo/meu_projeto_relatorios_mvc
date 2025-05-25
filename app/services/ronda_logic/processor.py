# processor.py
import logging
from datetime import datetime
from . import config
from .parser import parse_linha_log, extrair_detalhes_evento
from .processing import parear_eventos_ronda
from .report import formatar_relatorio_rondas

logger = logging.getLogger(__name__)

def processar_log_de_rondas(log_bruto_rondas_str: str,
                            nome_condominio_str: str,
                            data_plantao_manual_str: str = None,
                            escala_plantao_str: str = None): # escala_plantao_str é recebida aqui
    logger.info(f"Processando log de rondas para: {nome_condominio_str} (lógica interna)")
    if not log_bruto_rondas_str or not log_bruto_rondas_str.strip():
        logger.warning("Log de ronda bruto está vazio ou contém apenas espaços.")
        return "Nenhum log de ronda fornecido."

    data_para_relatorio_e_eventos = config.FALLBACK_DATA_INDEFINIDA
    if data_plantao_manual_str and data_plantao_manual_str.strip():
        partes = data_plantao_manual_str.strip().split('/')
        data_base_str = "/".join(partes[:3])
        try:
            datetime.strptime(data_base_str, "%d/%m/%Y")
            data_para_relatorio_e_eventos = data_base_str
        except ValueError:
            logger.warning(f"Data de plantão manual ('{data_plantao_manual_str}' -> interpretada como '{data_base_str}') é inválida ou não está no formato DD/MM/YYYY. Usando esta string '{data_base_str}' como está, similar ao JS.")
            data_para_relatorio_e_eventos = data_base_str

    log_bruto_rondas_str = log_bruto_rondas_str.replace('\\[', '[').replace('\\]', ']')
    logger.debug(f"Log bruto (após remover escapes de colchetes):\n{log_bruto_rondas_str[:500]}...")

    linhas = log_bruto_rondas_str.strip().split('\n')
    eventos_encontrados = []
    ultima_vtr_identificada = config.DEFAULT_VTR_ID

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip:
            continue

        _data_real_na_linha, id_vtr, mensagem, \
        _dummy_ultima_data_valida, ultima_vtr_identificada = \
            parse_linha_log(linha_strip,
                             None,
                             ultima_vtr_identificada,
                             data_para_relatorio_e_eventos)

        data_log_para_este_evento = data_para_relatorio_e_eventos
        logger.debug(f"Linha {i+1} Processada: Data para evento='{data_log_para_este_evento}', VTR='{id_vtr}', Msg='{mensagem}'")

        if not mensagem:
            logger.warning(f"Linha {i+1}: Mensagem para eventos vazia. Linha: '{linha_strip}'")
            continue

        evento = extrair_detalhes_evento(mensagem, data_log_para_este_evento, id_vtr, linha_original, ultima_vtr_identificada)
        if evento:
            eventos_encontrados.append(evento)
            logger.debug(f"  Evento parseado: {evento}")
        elif mensagem:
            logger.warning(f"  Nenhum evento de ronda (início/término com hora) reconhecido na mensagem: '{mensagem}' (linha original: '{linha_original}')")

    if not eventos_encontrados:
        if data_para_relatorio_e_eventos == config.FALLBACK_DATA_INDEFINIDA and not (data_plantao_manual_str and data_plantao_manual_str.strip()):
             logger.error("Nenhum evento de ronda válido identificado e nenhuma data de plantão válida foi fornecida para contextuailzar os eventos.")
        return "Nenhum evento de ronda válido (com data e hora) foi identificado no log fornecido."

    # REMOVER A LINHA ABAIXO PARA MANTER A ORDEM ORIGINAL DOS EVENTOS DO LOG
    # eventos_encontrados.sort(key=lambda e: e["datetime_obj"])

    rondas_pareadas, alertas_pareamento = parear_eventos_ronda(eventos_encontrados)

    if not rondas_pareadas and not alertas_pareamento:
        return "Eventos de ronda identificados, mas insuficientes para formar pares ou gerar alertas significativos." if eventos_encontrados else "Nenhum evento de ronda válido foi identificado no log fornecido."

    relatorio_final = formatar_relatorio_rondas(nome_condominio_str,
                                               data_para_relatorio_e_eventos,
                                               escala_plantao_str, # Passa a string original da escala
                                               eventos_encontrados,
                                               rondas_pareadas,
                                               alertas_pareamento)

    rondas_completas_count = sum(1 for r in rondas_pareadas if r.get("inicio_dt") and r.get("termino_dt"))
    logger.info(f"Relatório de rondas para {nome_condominio_str} formatado. {rondas_completas_count} rondas completas, {len(alertas_pareamento)} alertas.")
    return relatorio_final