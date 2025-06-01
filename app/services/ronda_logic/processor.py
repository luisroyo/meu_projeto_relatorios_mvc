# processor.py
import logging
import re
from datetime import datetime
from . import config
from .parser import parse_linha_log, extrair_detalhes_evento
from .processing import parear_eventos_ronda
from .report import formatar_relatorio_rondas

logger = logging.getLogger(__name__)

def processar_log_de_rondas(log_bruto_rondas_str: str,
                            nome_condominio_str: str,
                            data_plantao_manual_str: str = None,
                            escala_plantao_str: str = None):
    logger.info(f"Processando log de rondas para: {nome_condominio_str} (lógica interna de processamento)") # Alteração no log
    if not log_bruto_rondas_str or not log_bruto_rondas_str.strip():
        logger.warning("Log de ronda bruto está vazio ou contém apenas espaços.")
        return "Nenhum log de ronda fornecido ou log vazio." # Mensagem mais clara

    data_para_relatorio_e_eventos = config.FALLBACK_DATA_INDEFINIDA
    data_plantao_valida = False
    if data_plantao_manual_str and data_plantao_manual_str.strip():
        # Tenta limpar um pouco a data manual (ex: remover texto adicional, normalizar separadores)
        # Esta é uma limpeza simples; uma biblioteca de parsing de datas seria mais robusta para entradas muito variadas.
        data_limpa_match = re.search(r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})", data_plantao_manual_str)
        data_base_str_para_teste = data_plantao_manual_str.strip()

        if data_limpa_match:
            data_base_str_para_teste = data_limpa_match.group(1).replace('-', '/').replace('.', '/')
            partes = data_base_str_para_teste.split('/')
            if len(partes) == 3:
                # Ajusta ano com 2 dígitos para 4 dígitos (assume século 21)
                if len(partes[2]) == 2:
                    partes[2] = "20" + partes[2]
                data_base_str_para_teste = "/".join(partes)
        
        try:
            datetime.strptime(data_base_str_para_teste, "%d/%m/%Y")
            data_para_relatorio_e_eventos = data_base_str_para_teste
            data_plantao_valida = True
            logger.info(f"Data de plantão manual fornecida e validada: '{data_para_relatorio_e_eventos}' (original: '{data_plantao_manual_str}')")
        except ValueError:
            logger.warning(f"Data de plantão manual ('{data_plantao_manual_str}' -> interpretada como '{data_base_str_para_teste}') é inválida ou não está no formato DD/MM/YYYY. Será usada como fallback, o que pode impedir a criação de eventos.")
            # Se a data não é válida, manter o FALLBACK_DATA_INDEFINIDA pode ser mais seguro
            # do que usar uma string malformada que certamente falhará no strptime de cada evento.
            # No entanto, a lógica anterior era usar a string "como está".
            # Para maior robustez, se o parse falhar, é melhor considerar a data como indefinida
            # a menos que o comportamento desejado seja realmente usar a string literal.
            # Vou manter o comportamento de usar a string original problemática se o parse falhar,
            # mas com um aviso mais forte. O erro efetivo ocorrerá em extrair_detalhes_evento.
            data_para_relatorio_e_eventos = data_base_str_para_teste # Ou config.FALLBACK_DATA_INDEFINIDA se preferir falhar cedo
            # data_plantao_valida permanece False
    else:
        logger.info("Nenhuma data de plantão manual fornecida. A data dos eventos dependerá da extração de cada linha ou será indefinida.")


    # Sanitização do log bruto - remover escapes de colchetes e outros caracteres problemáticos se necessário
    # Cuidado com replace excessivo que pode corromper dados válidos.
    log_processado = log_bruto_rondas_str.replace('\\[', '[').replace('\\]', ']')
    # Adicionar mais replaces se outros padrões de "sujeira" forem comuns.
    # Ex: remover múltiplos espaços excessivos entre palavras, mas com cuidado.
    # log_processado = re.sub(r'\s{2,}', ' ', log_processado) # Exemplo: reduz múltiplos espaços a um único

    logger.debug(f"Log bruto (após sanitização inicial):\n{log_processado[:500]}...")

    linhas = log_processado.strip().split('\n')
    eventos_encontrados = []
    ultima_vtr_identificada = config.DEFAULT_VTR_ID

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip: # Pula linhas completamente vazias
            logger.debug(f"Linha {i+1} está vazia. Pulando.")
            continue

        # MUDANÇA IMPORTANTE: Se a data do plantão não foi validada E é essencial,
        # e data_para_relatorio_e_eventos ainda é FALLBACK_DATA_INDEFINIDA, então
        # cada evento não terá uma data válida.
        data_log_final_para_evento = data_para_relatorio_e_eventos
        if not data_plantao_valida and data_para_relatorio_e_eventos != config.FALLBACK_DATA_INDEFINIDA:
            # Se a data do plantão foi fornecida mas inválida, e estamos usando a string "como está",
            # ela provavelmente falhará em extrair_detalhes_evento.
            # Se nenhuma data de plantão foi dada, data_para_relatorio_e_eventos é FALLBACK_DATA_INDEFINIDA
            pass


        _data_real_na_linha, id_vtr, mensagem, \
        _dummy_ultima_data_valida, ultima_vtr_identificada = \
            parse_linha_log(linha_strip,
                             None, # _param_ultima_data_valida_ignorada
                             ultima_vtr_identificada,
                             data_log_final_para_evento) # Passa a data (válida ou não) para o parser

        logger.debug(f"Linha {i+1} Processada: Data para evento='{data_log_final_para_evento}', VTR='{id_vtr or ultima_vtr_identificada}', Msg='{mensagem}'")

        if not mensagem:
            logger.debug(f"Linha {i+1}: Mensagem para eventos vazia. Linha: '{linha_strip}'")
            continue

        # VTR a ser usada para o evento, garantindo que não seja None.
        vtr_para_evento = id_vtr if id_vtr else ultima_vtr_identificada
        if not vtr_para_evento or vtr_para_evento == config.DEFAULT_VTR_ID:
             # Se ainda for a VTR padrão, verificar se a mensagem pode conter uma VTR
             # Esta lógica já está no parser.py, mas pode ser reforçada aqui se necessário.
             pass


        evento = extrair_detalhes_evento(mensagem, data_log_final_para_evento, vtr_para_evento, linha_original, config.DEFAULT_VTR_ID) # Passa um fallback final para VTR
        if evento:
            eventos_encontrados.append(evento)
            logger.debug(f"  Evento parseado: {evento}")
        elif mensagem: # Apenas loga se havia uma mensagem mas nenhum evento foi extraído
            logger.info(f"  Nenhum evento de ronda (início/término com hora) reconhecido na mensagem: '{mensagem}' (linha original: '{linha_original}')")

    if not eventos_encontrados:
        msg_retorno = "Nenhum evento de ronda válido (com data e hora reconhecíveis) foi identificado no log fornecido."
        if not data_plantao_valida and not (data_plantao_manual_str and data_plantao_manual_str.strip()):
             logger.error("Nenhum evento de ronda válido identificado E nenhuma data de plantão válida foi fornecida para contextualizar os eventos.")
             msg_retorno += " A data do plantão também não foi fornecida ou é inválida."
        elif not data_plantao_valida and (data_plantao_manual_str and data_plantao_manual_str.strip()):
             logger.error(f"Nenhum evento de ronda válido identificado E a data de plantão fornecida ('{data_plantao_manual_str}') é inválida.")
             msg_retorno += f" A data do plantão fornecida ('{data_plantao_manual_str}') é inválida."

        return msg_retorno

    rondas_pareadas, alertas_pareamento = parear_eventos_ronda(eventos_encontrados)

    if not rondas_pareadas and not alertas_pareamento and eventos_encontrados: # Havia eventos, mas não formaram rondas nem alertas
        return "Eventos de ronda identificados, mas insuficientes para formar pares de início/término ou gerar alertas significativos."
    elif not rondas_pareadas and not alertas_pareamento and not eventos_encontrados: # Nenhum evento (já tratado acima, mas para cobrir)
        return "Nenhum evento de ronda válido foi identificado no log fornecido."


    relatorio_final = formatar_relatorio_rondas(nome_condominio_str,
                                               data_para_relatorio_e_eventos if data_plantao_valida else config.FALLBACK_DATA_INDEFINIDA, # Usa data validada ou fallback
                                               escala_plantao_str, 
                                               eventos_encontrados,
                                               rondas_pareadas,
                                               alertas_pareamento)

    rondas_completas_count = sum(1 for r in rondas_pareadas if r.get("inicio_dt") and r.get("termino_dt"))
    logger.info(f"Relatório de rondas para {nome_condominio_str} formatado. {rondas_completas_count} rondas completas, {len(alertas_pareamento)} alertas.")
    return relatorio_final