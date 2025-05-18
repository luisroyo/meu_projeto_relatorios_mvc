import re
from datetime import datetime, timedelta, timezone # Mantendo suas importações originais
import logging

logger = logging.getLogger(__name__)

def _normalizar_hora_capturada(hora_str_raw: str) -> str:
    """Normaliza uma string de hora capturada (ex: '18 : 48', '7:00') para HH:MM."""
    if hora_str_raw is None:
        return ""
    hora_str_limpa = "".join(hora_str_raw.split()) # Remove todos os espaços
    if ":" not in hora_str_limpa:
        # Tenta converter formatos como "700" para "07:00" ou "1848" para "18:48"
        if len(hora_str_limpa) == 3 and hora_str_limpa.isdigit():
            hora_str_limpa = f"0{hora_str_limpa[0]}:{hora_str_limpa[1:]}"
        elif len(hora_str_limpa) == 4 and hora_str_limpa.isdigit():
            hora_str_limpa = f"{hora_str_limpa[:2]}:{hora_str_limpa[2:]}"
        else: # Se não for um formato numérico esperado, não tenta adivinhar
            logger.warning(f"Formato de hora sem ':' e não numérico esperado: '{hora_str_raw}'")
            return hora_str_raw 
    
    parts = hora_str_limpa.split(':')
    if len(parts) == 2:
        try:
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59): # Validação básica da hora
                logger.warning(f"Valores de hora/minuto fora do intervalo: '{hora_str_raw}' -> H:{h}, M:{m}")
                return hora_str_raw 
            return f"{h:02d}:{m:02d}" 
        except ValueError:
            logger.warning(f"Formato de hora inválido após limpeza inicial: '{hora_str_limpa}'")
            return hora_str_raw 
    logger.warning(f"Formato de hora não reconhecido para normalização: '{hora_str_raw}'")
    return hora_str_raw 


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
    ultima_vtr_identificada = "VTR_DESCONHECIDA" # Para casos onde a VTR não é clara na linha

    # Regex para extrair data DD/MM/YYYY de dentro de colchetes no início da linha.
    # Torna a parte da hora antes da data opcional e mais flexível.
    regex_prefixo_linha = re.compile(
        r"^\s*\["                          # Início da linha e '['
        r"(?:[^,\]]*?)"                    # Qualquer coisa que não seja vírgula ou ']', opcional (para a hora do prefixo)
        r"(?:[, ]\s*| )?"                  # Separador opcional (vírgula ou espaço) ou apenas um espaço
        r"(\d{1,2}/\d{1,2}/\d{4})\s*"      # Grupo 1: Data do log (DD/MM/YYYY)
        r"\]\s*"                           # Fim do ']' do prefixo
        r"(?:(VTR\s*\d+):\s*)?"            # Grupo 2 (opcional): Identificador da VTR (ex: "VTR 05:")
        r"(.*)$",                          # Grupo 3: Restante da mensagem
        re.IGNORECASE
    )
    
    # Regex alternativas para linhas que não casam com o formato completo de prefixo
    # Tenta pegar VTR e mensagem se o prefixo de data não for encontrado da forma usual.
    regex_vtr_mensagem_alternativa = re.compile(r"^(VTR\s*\d+):\s*(.*)$", re.IGNORECASE)


    regexes_evento_python = [
        # Prioriza regexes que pegam a hora no início da mensagem do evento
        {"tipo": "inicio", "regex": re.compile(r"(\d{1,2}\s*:\s*\d{2}).*?(?:in[ií]cio|inicio)(?:s\sde\s|\sde\s|\s)ronda", re.IGNORECASE)},
        {"tipo": "termino", "regex": re.compile(r"(\d{1,2}\s*:\s*\d{2}).*?(?:t[ée]rmino|termino)(?:s\sde\s|\sde\s|\s)ronda", re.IGNORECASE)},
        {"tipo": "inicio", "regex": re.compile(r"(\d{1,2}\s*:\s*\d{2}).*?(?:in[ií]cio|inicio)", re.IGNORECASE)}, # Mais genérico
        {"tipo": "termino", "regex": re.compile(r"(\d{1,2}\s*:\s*\d{2}).*?(?:t[ée]rmino|termino)", re.IGNORECASE)}, # Mais genérico
        
        # Regexes que pegam a hora no final da frase do evento
        {"tipo": "inicio", "regex": re.compile(r"(?:in[ií]cio|inicio)(?:s\sde\s|\sde\s|\s)ronda.*?\s+(\d{1,2}\s*:\s*\d{2})", re.IGNORECASE)},
        {"tipo": "termino", "regex": re.compile(r"(?:t[ée]rmino|termino)(?:s\sde\s|\sde\s|\s)ronda.*?\s+(\d{1,2}\s*:\s*\d{2})", re.IGNORECASE)},
        {"tipo": "inicio", "regex": re.compile(r"(?:in[ií]cio|inicio).*?\s+(\d{1,2}\s*:\s*\d{2})", re.IGNORECASE)}, # Mais genérico
        {"tipo": "termino", "regex": re.compile(r"(?:t[ée]rmino|termino).*?\s+(\d{1,2}\s*:\s*\d{2})", re.IGNORECASE)}, # Mais genérico
    ]

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip()
        if not linha_strip:
            continue

        log_data_str_linha = None
        vtr_id_str_linha = None
        mensagem_para_eventos = None

        match_prefixo = regex_prefixo_linha.match(linha_strip)
        if match_prefixo:
            log_data_str_linha = match_prefixo.group(1)
            vtr_id_str_linha = match_prefixo.group(2) # Pode ser None se não casar
            mensagem_para_eventos = match_prefixo.group(3).strip()
            
            if vtr_id_str_linha:
                vtr_id_str_linha = vtr_id_str_linha.upper().replace(" ", "")
                ultima_vtr_identificada = vtr_id_str_linha
            else: # VTR não estava no prefixo, tenta pegar da última VTR ou da mensagem
                match_vtr_na_msg = regex_vtr_mensagem_alternativa.match(mensagem_para_eventos)
                if match_vtr_na_msg:
                    vtr_id_str_linha = match_vtr_na_msg.group(1).upper().replace(" ", "")
                    mensagem_para_eventos = match_vtr_na_msg.group(2).strip() # Atualiza mensagem
                    ultima_vtr_identificada = vtr_id_str_linha
                else:
                    vtr_id_str_linha = ultima_vtr_identificada # Usa a última VTR conhecida
            
            ultima_data_valida_extraida = log_data_str_linha
            logger.debug(f"Linha {i+1} (Match Prefixo): Data='{log_data_str_linha}', VTR='{vtr_id_str_linha}', Msg='{mensagem_para_eventos}'")
        else:
            # Se o prefixo completo não casar, ainda tenta pegar VTR e mensagem
            # e usa a última data válida ou a data do plantão
            log_data_str_linha = ultima_data_valida_extraida or data_plantao_manual_str
            if not log_data_str_linha:
                logger.warning(f"Linha {i+1}: Não foi possível determinar data para: '{linha_strip}'. Pulando.")
                continue

            match_vtr_msg_alt = regex_vtr_mensagem_alternativa.match(linha_strip)
            if match_vtr_msg_alt:
                vtr_id_str_linha = match_vtr_msg_alt.group(1).upper().replace(" ", "")
                mensagem_para_eventos = match_vtr_msg_alt.group(2).strip()
                ultima_vtr_identificada = vtr_id_str_linha
                logger.debug(f"Linha {i+1} (Match VTR Alternativo): Data='{log_data_str_linha}', VTR='{vtr_id_str_linha}', Msg='{mensagem_para_eventos}'")
            else:
                # Se nem VTR for encontrada, considera a linha toda como mensagem e usa a última VTR
                mensagem_para_eventos = linha_strip
                vtr_id_str_linha = ultima_vtr_identificada
                logger.debug(f"Linha {i+1} (Sem match VTR): Data='{log_data_str_linha}', VTR='{vtr_id_str_linha}', Msg='{mensagem_para_eventos}'")
        
        if not mensagem_para_eventos:
            logger.warning(f"Linha {i+1}: Mensagem para eventos vazia. Linha: '{linha_strip}'")
            continue
            
        evento_na_linha = None
        for r_info in regexes_evento_python:
            match_evento = r_info["regex"].search(mensagem_para_eventos)
            if match_evento:
                hora_evento_str_raw = match_evento.group(1)
                hora_evento_formatada = _normalizar_hora_capturada(hora_evento_str_raw)
                
                if hora_evento_formatada: 
                    # Garante que log_data_str_linha tem um valor antes de usar
                    data_para_datetime = log_data_str_linha
                    if not data_para_datetime: # Fallback final se tudo falhar
                        logger.error(f"Data para evento não pôde ser determinada para linha: '{linha_original}' com hora '{hora_evento_formatada}'")
                        continue

                    dt_evento_str = f"{data_para_datetime} {hora_evento_formatada}"
                    try:
                        dt_obj = datetime.strptime(dt_evento_str, "%d/%m/%Y %H:%M")
                        evento_na_linha = {
                            "vtr": vtr_id_str_linha or ultima_vtr_identificada, # Garante que VTR tenha um valor
                            "tipo": r_info["tipo"],
                            "hora_str": hora_evento_formatada,
                            "data_str": data_para_datetime,
                            "datetime_obj": dt_obj,
                            "linha_original": linha_original
                        }
                        logger.debug(f"  Evento parseado: {evento_na_linha}")
                        break 
                    except ValueError as ve:
                        logger.error(f"  Erro de data/hora ao parsear evento '{linha_original}': {ve}. Data str: '{data_para_datetime}', Hora formatada: '{hora_evento_formatada}'")
        
        if evento_na_linha:
            eventos_encontrados.append(evento_na_linha)
        else:
            logger.warning(f"  Nenhum evento de ronda (início/término com hora) reconhecido na mensagem: '{mensagem_para_eventos}' (linha original: '{linha_original}')")

    if not eventos_encontrados:
        return "Nenhum evento de ronda válido (com data e hora) foi identificado no log fornecido."

    eventos_encontrados.sort(key=lambda e: e["datetime_obj"])

    # Lógica de Pareamento (mantida como no seu código fornecido no artefato)
    rondas_pareadas = []
    inicio_pendente = None
    alertas_pareamento = []

    for evento in eventos_encontrados:
        if evento["tipo"] == "inicio":
            if inicio_pendente:
                if inicio_pendente["vtr"] == evento["vtr"]:
                    alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') sem término correspondente antes de novo início (Linha: '{evento['linha_original']}').")
                    rondas_pareadas.append({
                        "inicio_dt": inicio_pendente["datetime_obj"],
                        "termino_dt": None, 
                        "vtr": inicio_pendente["vtr"]
                    })
                elif inicio_pendente["vtr"] != evento["vtr"]:
                     alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') ainda pendente ao encontrar início de {evento['vtr']}.")
            inicio_pendente = evento
        elif evento["tipo"] == "termino":
            if inicio_pendente:
                if inicio_pendente["vtr"] == evento["vtr"]: 
                    rondas_pareadas.append({
                        "inicio_dt": inicio_pendente["datetime_obj"],
                        "termino_dt": evento["datetime_obj"],
                        "vtr": inicio_pendente["vtr"]
                    })
                    inicio_pendente = None
                else: 
                    alertas_pareamento.append(f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} (Linha: '{evento['linha_original']}') mas início pendente era de {inicio_pendente['vtr']} (Linha: '{inicio_pendente['linha_original']}').")
                    rondas_pareadas.append({ "inicio_dt": None, "termino_dt": evento["datetime_obj"], "vtr": evento["vtr"] })
            else: 
                alertas_pareamento.append(f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} (Linha: '{evento['linha_original']}') sem início correspondente.")
                rondas_pareadas.append({ "inicio_dt": None, "termino_dt": evento["datetime_obj"], "vtr": evento["vtr"] })

    if inicio_pendente: 
        alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} (Linha: '{inicio_pendente['linha_original']}') sem término correspondente no final do log.")
        rondas_pareadas.append({ "inicio_dt": inicio_pendente["datetime_obj"], "termino_dt": None, "vtr": inicio_pendente["vtr"] })

    # Formatação da Saída Final
    if not rondas_pareadas and not alertas_pareamento:
        if eventos_encontrados:
             return "Eventos de ronda identificados, mas insuficientes para formar pares ou gerar alertas significativos."
        return "Nenhum evento de ronda válido foi identificado no log fornecido."
    
    if data_plantao_manual_str:
        try:
            dt_plantao_obj = datetime.strptime(data_plantao_manual_str.strip(), "%d/%m/%Y")
            data_final_plantao_str = dt_plantao_obj.strftime("%d/%m/%Y")
        except ValueError:
            logger.warning(f"Data de plantão manual ('{data_plantao_manual_str}') inválida.")
            if eventos_encontrados: data_final_plantao_str = eventos_encontrados[0]["datetime_obj"].strftime("%d/%m/%Y")
            else: data_final_plantao_str = "[Data Indefinida]"
    elif eventos_encontrados: data_final_plantao_str = eventos_encontrados[0]["datetime_obj"].strftime("%d/%m/%Y")
    else: data_final_plantao_str = "[Data Indefinida]"

    escala_final_str = escala_plantao_str if escala_plantao_str else "[Escala não Informada]"
    
    linhas_saida = []
    linhas_saida.append(f"Plantão {data_final_plantao_str} ({escala_final_str})")
    linhas_saida.append(f"          Projeto Mais com Menos") # LINHA ADICIONADA
    linhas_saida.append(f"\n      📍 Residencial: {nome_condominio_str}\n") # ALTERADO "Condomínio" para "Residencial" e adicionado recuo

    rondas_completas_count = 0
    rondas_exibidas = False
    for ronda in rondas_pareadas:
        if ronda.get("inicio_dt"):
            inicio_fmt = ronda["inicio_dt"].strftime("%H:%M")
            termino_fmt = ronda["termino_dt"].strftime("%H:%M") if ronda.get("termino_dt") else "[PENDENTE]"
            if ronda.get("termino_dt"): rondas_completas_count += 1
            # REMOVIDO (VTR: {ronda['vtr']}) da linha abaixo
            linhas_saida.append(f"\tInício: {inicio_fmt:<7}– Término: {termino_fmt:<7}") 
            rondas_exibidas = True
        # A lógica para términos órfãos foi mantida para os alertas, mas não para exibição principal aqui

    if not rondas_exibidas and not alertas_pareamento:
         linhas_saida.append("\tNenhuma ronda para exibir (verifique alertas).")
    elif not rondas_exibidas and alertas_pareamento:
         linhas_saida.append("\tNenhuma ronda completa para exibir (verifique alertas).")

    linhas_saida.append(f"\n✅ Total: {rondas_completas_count} rondas completas no plantão")

    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:")
        linhas_saida.extend(alertas_pareamento)
    
    logger.info(f"Relatório de rondas para {nome_condominio_str} formatado. {rondas_completas_count} rondas completas, {len(alertas_pareamento)} alertas.")
    return "\n".join(linhas_saida)

