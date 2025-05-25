# parser.py
import logging
from datetime import datetime
from . import config # Importa config.py do mesmo diretório (ronda_logic)
from .utils import normalizar_hora_capturada # Importa de utils.py do mesmo diretório

logger = logging.getLogger(__name__)

# Assinatura modificada: _param_ultima_data_valida_ignorada para indicar que não é mais usada para definir a data do evento.
# data_fixa_para_eventos é a data que será usada para o evento.
def parse_linha_log(linha_strip: str,
                    _param_ultima_data_valida_ignorada: str, # Nome alterado para clareza
                    ultima_vtr: str,
                    data_fixa_para_eventos: str): # Esta é a data que será atribuída ao log/evento
    
    data_log_atribuida = data_fixa_para_eventos # MUDANÇA CRUCIAL: A data do log é a data fixa fornecida
    id_vtr_linha = None
    mensagem_eventos = None
    data_original_na_linha = None # Para armazenar a data original da linha, se houver (para o 4º item do retorno)

    match_prefixo = config.REGEX_PREFIXO_LINHA.match(linha_strip)
    if match_prefixo:
        data_original_na_linha = match_prefixo.group(1) # Data original da linha (não usada para data_log_atribuida)
        vtr_match = match_prefixo.group(2)
        mensagem_eventos = match_prefixo.group(3).strip()
        
        if vtr_match:
            id_vtr_linha = vtr_match.upper().replace(" ", "")
            ultima_vtr = id_vtr_linha
        else: # Sem VTR no prefixo, tenta na mensagem
            match_vtr_msg = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(mensagem_eventos)
            if match_vtr_msg:
                id_vtr_linha = match_vtr_msg.group(1).upper().replace(" ", "")
                mensagem_eventos = match_vtr_msg.group(2).strip()
                ultima_vtr = id_vtr_linha
            else: # Nenhuma VTR específica encontrada
                id_vtr_linha = ultima_vtr
    else: # Sem prefixo padrão
        # data_log_atribuida permanece data_fixa_para_eventos
        match_vtr_msg_alt = config.REGEX_VTR_MENSAGEM_ALTERNATIVA.match(linha_strip)
        if match_vtr_msg_alt:
            id_vtr_linha = match_vtr_msg_alt.group(1).upper().replace(" ", "")
            mensagem_eventos = match_vtr_msg_alt.group(2).strip()
            ultima_vtr = id_vtr_linha
        else: # Linha inteira é mensagem
            mensagem_eventos = linha_strip
            id_vtr_linha = ultima_vtr
            
    # Retorna a data_log_atribuida (que é a data_fixa_para_eventos), VTR, mensagem.
    # O quarto valor retornado (originalmente ultima_data_valida) pode ser a data original da linha
    # ou o _param_ultima_data_valida_ignorada se nenhuma data foi encontrada na linha.
    # Isso minimiza mudanças na desestruturação da tupla no processor.py, embora esse valor
    # não seja mais usado pelo processor para determinar a data do próximo evento.
    quarto_valor_retorno = data_original_na_linha if data_original_na_linha else _param_ultima_data_valida_ignorada
    return data_log_atribuida, id_vtr_linha, mensagem_eventos, quarto_valor_retorno, ultima_vtr

# extrair_detalhes_evento permanece o mesmo, pois já recebe data_log como parâmetro
# e tentará criar o datetime_obj. Se data_log (que agora será data_fixa_para_eventos)
# for inválida (ex: config.FALLBACK_DATA_INDEFINIDA ou uma string malformada),
# a criação do datetime_obj falhará e será logado, o que é um comportamento aceitável.
def extrair_detalhes_evento(mensagem: str, data_log: str, id_vtr: str, linha_original_str: str, vtr_fallback: str):
    if not mensagem:
        return None

    for r_info in config.COMPILED_RONDA_EVENT_REGEXES: # Usa config.
        match_evento = r_info["regex"].search(mensagem)
        if match_evento:
            hora_evento_raw = match_evento.group(1)
            hora_formatada = normalizar_hora_capturada(hora_evento_raw) # Usa de .utils
            
            if hora_formatada and data_log: # data_log aqui será a data_fixa_para_eventos
                # Verifica se data_log é uma string de data potencialmente válida antes de tentar criar datetime
                if data_log == config.FALLBACK_DATA_INDEFINIDA:
                    logger.error(f"  Não é possível criar data/hora para evento '{linha_original_str}' porque a data do plantão é indefinida ('{data_log}').")
                    return None

                dt_evento_str = f"{data_log} {hora_formatada}"
                try:
                    dt_obj = datetime.strptime(dt_evento_str, "%d/%m/%Y %H:%M")
                    return {
                        "vtr": id_vtr or vtr_fallback,
                        "tipo": r_info["tipo"],
                        "hora_str": hora_formatada,
                        "data_str": data_log,
                        "datetime_obj": dt_obj,
                        "linha_original": linha_original_str
                    }
                except ValueError as ve:
                    logger.error(f"  Erro de data/hora ao parsear evento '{linha_original_str}': {ve}. Data str fornecida: '{data_log}', Hora formatada: '{hora_formatada}'")
                    return None
    return None