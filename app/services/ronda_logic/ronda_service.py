import logging
# from datetime import datetime, timedelta, timezone # Não são mais usadas diretamente aqui

# Importações dos módulos criados
from . import ronda_config # Ou 'import ronda_config'
from .ronda_parser import parse_linha_log, extrair_detalhes_evento
from .ronda_processing import parear_eventos_ronda
from .ronda_report import formatar_relatorio_rondas
# A função normalizar_hora_capturada é usada internamente por ronda_parser

logger = logging.getLogger(__name__)

def processar_log_de_rondas(log_bruto_rondas_str: str, 
                            nome_condominio_str: str, 
                            data_plantao_manual_str: str = None, 
                            escala_plantao_str: str = None):
    """
    Processa um bloco de texto de log de rondas e retorna um relatório formatado.
    """
    logger.info(f"Iniciando processamento de log de rondas para o condomínio: {nome_condominio_str}")
    if not log_bruto_rondas_str or not log_bruto_rondas_str.strip():
        logger.warning("Log de ronda bruto está vazio ou contém apenas espaços.")
        return "Nenhum log de ronda fornecido."

    log_bruto_rondas_str = log_bruto_rondas_str.replace('\\[', '[').replace('\\]', ']')
    logger.debug(f"Log bruto (após remover escapes de colchetes):\n{log_bruto_rondas_str[:500]}...")

    linhas = log_bruto_rondas_str.strip().split('\n')
    eventos_encontrados = []
    ultima_data_valida_extraida = None
    ultima_vtr_identificada = ronda_config.DEFAULT_VTR_ID # Usando constante

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip:
            continue

        data_log, id_vtr, mensagem, \
        ultima_data_valida_extraida, ultima_vtr_identificada = \
            parse_linha_log(linha_strip, ultima_data_valida_extraida, 
                             ultima_vtr_identificada, data_plantao_manual_str)

        if not data_log:
            logger.warning(f"Linha {i+1}: Não foi possível determinar data para: '{linha_strip}'. Pulando.")
            continue
        
        logger.debug(f"Linha {i+1} Parsed: Data='{data_log}', VTR='{id_vtr}', Msg='{mensagem}'")

        if not mensagem:
            logger.warning(f"Linha {i+1}: Mensagem para eventos vazia. Linha: '{linha_strip}'")
            continue
            
        evento = extrair_detalhes_evento(mensagem, data_log, id_vtr, linha_original, ultima_vtr_identificada)
        if evento:
            eventos_encontrados.append(evento)
            logger.debug(f"  Evento parseado: {evento}")
        elif mensagem: 
            logger.warning(f"  Nenhum evento de ronda (início/término com hora) reconhecido na mensagem: '{mensagem}' (linha original: '{linha_original}')")

    if not eventos_encontrados:
        return "Nenhum evento de ronda válido (com data e hora) foi identificado no log fornecido."

    eventos_encontrados.sort(key=lambda e: e["datetime_obj"])

    rondas_pareadas, alertas_pareamento = parear_eventos_ronda(eventos_encontrados)

    if not rondas_pareadas and not alertas_pareamento:
        return "Eventos de ronda identificados, mas insuficientes para formar pares ou gerar alertas significativos." if eventos_encontrados else "Nenhum evento de ronda válido foi identificado no log fornecido."
    
    relatorio_final = formatar_relatorio_rondas(nome_condominio_str, data_plantao_manual_str, 
                                               escala_plantao_str, eventos_encontrados, 
                                               rondas_pareadas, alertas_pareamento)
    
    rondas_completas_count = sum(1 for r in rondas_pareadas if r.get("inicio_dt") and r.get("termino_dt"))
    logger.info(f"Relatório de rondas para {nome_condominio_str} formatado. {rondas_completas_count} rondas completas, {len(alertas_pareamento)} alertas.")
    return relatorio_final

# Exemplo de como usar (pode estar em um arquivo separado ou aqui para teste)
if __name__ == '__main__':
    # Configuração básica do logger para ver as saídas
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_exemplo = """
    [10:30, 20/05/2024] VTR 01: Início ronda 10:30
    [11:00, 20/05/2024] VTR 01: Término ronda 11 : 00
    [12:00, 20/05/2024] VTR 02: inicio de ronda as 1200
    [20/05/2024] VTR 02: termino de ronda as 12:30
    [14:00 20/05/2024] VTR 01: Início 14:00
    """
    
    nome_condominio = "Residencial Teste"
    data_plantao = "20/05/2024"
    escala = "Equipe Demo"
    
    relatorio = processar_log_de_rondas(log_exemplo, nome_condominio, data_plantao, escala)
    print("\n--- RELATÓRIO GERADO ---")
    print(relatorio)