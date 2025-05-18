import re
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

def _normalizar_hora_capturada(hora_str_raw: str) -> str:
    """Normaliza uma string de hora capturada (ex: '18 : 48', '7:00') para HH:MM."""
    if hora_str_raw is None:
        return ""
    hora_str_limpa = "".join(hora_str_raw.split()) # Remove todos os espaços
    if ":" not in hora_str_limpa:
        if len(hora_str_limpa) == 3: # ex "700" -> "07:00"
            hora_str_limpa = f"0{hora_str_limpa[0]}:{hora_str_limpa[1:]}"
        elif len(hora_str_limpa) == 4: # ex "1848" -> "18:48"
            hora_str_limpa = f"{hora_str_limpa[:2]}:{hora_str_limpa[2:]}"
        # Adicionar mais lógicas de normalização se necessário
    
    parts = hora_str_limpa.split(':')
    if len(parts) == 2:
        try:
            h, m = int(parts[0]), int(parts[1])
            return f"{h:02d}:{m:02d}" # Formata com zeros à esquerda
        except ValueError:
            logger.warning(f"Formato de hora inválido após limpeza inicial: '{hora_str_limpa}'")
            return hora_str_raw # Retorna o original se não puder formatar
    logger.warning(f"Formato de hora não reconhecido para normalização: '{hora_str_raw}'")
    return hora_str_raw # Retorna o original se não for HH:MM


# Dentro de app/services/ronda_service.py

# ... (importações e a função _normalizar_hora_capturada permanecem as mesmas) ...

def processar_log_de_rondas(log_bruto_rondas_str: str, 
                            nome_condominio_str: str, 
                            data_plantao_manual_str: str = None, 
                            escala_plantao_str: str = None):
    """
    Processa um bloco de texto de log de rondas e retorna um relatório formatado.
    data_plantao_manual_str: ex, "12/05/2025" (fornecida pelo usuário)
    escala_plantao_str: ex, "18-06" ou "06-18" (fornecida pelo usuário)
    """
    logger.info(f"Iniciando processamento de log de rondas para o condomínio: {nome_condominio_str}")
    if not log_bruto_rondas_str or not log_bruto_rondas_str.strip():
        logger.warning("Log de ronda bruto está vazio ou contém apenas espaços.")
        return "Nenhum log de ronda fornecido."

    # --- ADICIONAR ESTA LINHA DE PRÉ-PROCESSAMENTO ---
    log_bruto_rondas_str = log_bruto_rondas_str.replace('\\[', '[').replace('\\]', ']')
    # ----------------------------------------------------

    logger.debug(f"Log bruto (após remover escapes de colchetes):\n{log_bruto_rondas_str[:500]}...")

    linhas = log_bruto_rondas_str.strip().split('\n')
    eventos_encontrados = []

    # Regex para a estrutura geral da linha de log: [HH:MM, DD/MM/YYYY] VTR XX: MENSAGEM
    regex_linha_completa = re.compile(
        r"^\s*\[(\d{1,2}:\d{1,2}),\s*(\d{1,2}/\d{1,2}/\d{4})\]\s*"
        r"(VTR\s*\d+):\s*" 
        r"(.*)$",
        re.IGNORECASE
    )

    regexes_evento_python = [
        {"tipo": "inicio", "regex": re.compile(r"(\d{1,2}\s*:\s*\d{2}).*?(?:in[ií]cio|inicio)(?:\s+de\s+ronda)?", re.IGNORECASE)},
        {"tipo": "termino", "regex": re.compile(r"(\d{1,2}\s*:\s*\d{2}).*?(?:t[ée]rmino|termino)(?:\s+de\s+ronda)?", re.IGNORECASE)},
        {"tipo": "inicio", "regex": re.compile(r"(?:in[ií]cio|inicio)\s+de\s+ronda.*?\s+(\d{1,2}\s*:\s*\d{2})", re.IGNORECASE)},
        {"tipo": "termino", "regex": re.compile(r"(?:t[ée]rmino|termino)\s+de\s+ronda.*?\s+(\d{1,2}\s*:\s*\d{2})", re.IGNORECASE)}
    ]

    for i, linha_original in enumerate(linhas):
        linha_strip = linha_original.strip() # linha_strip já foi feito, mas ok repetir
        if not linha_strip:
            continue

        # A linha de log que o logger mostra é a linha_original (ou linha_strip antes da regex)
        # Precisamos garantir que a regex_linha_completa use a linha sem os escapes se eles existirem
        # O pré-processamento acima já deve ter cuidado disso para todas as 'linhas'.

        match_linha_completa = regex_linha_completa.match(linha_strip) # Usar linha_strip
        if not match_linha_completa:
            logger.warning(f"Linha {i+1} não corresponde ao formato de log esperado (sem prefixo [data,hora] VTR XX): '{linha_strip}'")
            continue

        log_data_str = match_linha_completa.group(2) 
        vtr_id_str = match_linha_completa.group(3).upper().replace(" ", "") 
        mensagem_vtr = match_linha_completa.group(4).strip() 
        
        evento_na_linha = None
        for r_info in regexes_evento_python:
            match_evento = r_info["regex"].search(mensagem_vtr)
            if match_evento:
                hora_evento_str_raw = match_evento.group(1)
                hora_evento_formatada = _normalizar_hora_capturada(hora_evento_str_raw)
                
                if hora_evento_formatada: 
                    dt_evento_str = f"{log_data_str} {hora_evento_formatada}"
                    try:
                        dt_obj = datetime.strptime(dt_evento_str, "%d/%m/%Y %H:%M")
                        evento_na_linha = {
                            "vtr": vtr_id_str,
                            "tipo": r_info["tipo"],
                            "hora_str": hora_evento_formatada,
                            "data_str": log_data_str,
                            "datetime_obj": dt_obj,
                            "linha_original": linha_original
                        }
                        logger.debug(f"Evento parseado: {evento_na_linha}")
                        break 
                    except ValueError as ve:
                        logger.error(f"Erro de data/hora ao parsear evento '{linha_original}': {ve}. Data str: '{log_data_str}', Hora formatada: '{hora_evento_formatada}'")
        
        if evento_na_linha:
            eventos_encontrados.append(evento_na_linha)
        else:
            logger.warning(f"Nenhum evento de ronda (início/término com hora) reconhecido na mensagem: '{mensagem_vtr}' (linha original: '{linha_original}')")

    if not eventos_encontrados:
        return "Nenhum evento de ronda válido (com data e hora) foi identificado no log fornecido."

    eventos_encontrados.sort(key=lambda e: e["datetime_obj"])

    # ... (o restante da função: Pareamento de Início e Término, Formatação da Saída Final) ...
    # Essa parte do código que você já tem (e eu forneci na última versão completa do ronda_service.py)
    # permanece a mesma. Apenas a linha de pré-processamento no início da função foi adicionada.

    # --- Lógica de Pareamento (igual à anterior) ---
    rondas_pareadas = [] # Renomeado de rondas_pareadas_completas para consistência
    inicio_pendente = None # Renomeado de inicio_pendente_obj para consistência
    alertas_pareamento = []

    for evento in eventos_encontrados:
        if evento["tipo"] == "inicio":
            if inicio_pendente:
                if inicio_pendente["vtr"] == evento["vtr"]:
                    alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} sem término correspondente antes de novo início.")
                    rondas_pareadas.append({
                        "inicio_dt": inicio_pendente["datetime_obj"],
                        "termino_dt": None, 
                        "vtr": inicio_pendente["vtr"]
                    })
            inicio_pendente = evento
        elif evento["tipo"] == "termino" and inicio_pendente:
            if inicio_pendente["vtr"] == evento["vtr"]: 
                rondas_pareadas.append({
                    "inicio_dt": inicio_pendente["datetime_obj"],
                    "termino_dt": evento["datetime_obj"],
                    "vtr": inicio_pendente["vtr"]
                })
                inicio_pendente = None
            else: 
                alertas_pareamento.append(f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} mas início pendente era de {inicio_pendente['vtr']}.")
        elif evento["tipo"] == "termino" and not inicio_pendente:
             alertas_pareamento.append(f"⚠️ Término de ronda para {evento['vtr']} às {evento['data_str']} {evento['hora_str']} sem início correspondente.")

    if inicio_pendente: 
        alertas_pareamento.append(f"⚠️ Início de ronda para {inicio_pendente['vtr']} às {inicio_pendente['data_str']} {inicio_pendente['hora_str']} sem término correspondente no final do log.")
        rondas_pareadas.append({
            "inicio_dt": inicio_pendente["datetime_obj"],
            "termino_dt": None,
            "vtr": inicio_pendente["vtr"]
        })
    # --- Fim da Lógica de Pareamento ---

    # --- Formatação da Saída Final (igual à anterior) ---
    if not rondas_pareadas and not alertas_pareamento:
         return "Nenhum evento de ronda válido foi identificado no log fornecido e nenhum alerta de pareamento gerado."
    if not rondas_pareadas and alertas_pareamento:
        return f"Problemas ao processar o log de rondas:\n" + "\n".join(alertas_pareamento)

    data_final_plantao_str = ""
    if data_plantao_manual_str:
        try:
            dt_plantao_obj = datetime.strptime(data_plantao_manual_str.strip(), "%d/%m/%Y")
            data_final_plantao_str = dt_plantao_obj.strftime("%d/%m/%Y")
        except ValueError:
            logger.warning(f"Data de plantão manual ('{data_plantao_manual_str}') inválida. Usando data da primeira ronda se possível.")
            if rondas_pareadas: # Verifica se rondas_pareadas não está vazia
                 data_final_plantao_str = rondas_pareadas[0]["inicio_dt"].strftime("%d/%m/%Y")
            else:
                 data_final_plantao_str = "[Data Indefinida]"
    elif rondas_pareadas:
        data_final_plantao_str = rondas_pareadas[0]["inicio_dt"].strftime("%d/%m/%Y")
    else:
        data_final_plantao_str = "[Sem Rondas para Definir Data]"

    escala_final_str = "[Escala não Informada]"
    if escala_plantao_str:
        escala_parts = escala_plantao_str.strip().split('-')
        if len(escala_parts) == 2:
            try: # Adiciona try-except para conversão de hora
                escala_inicio = int(escala_parts[0])
                escala_fim = int(escala_parts[1])
                escala_final_str = f"{escala_inicio:02d}h às {escala_fim:02d}h"
            except ValueError:
                 logger.warning(f"Escala de plantão ('{escala_plantao_str}') com formato de hora inválido. Usando como string.")
                 escala_final_str = f"({escala_plantao_str})"
        else:
            escala_final_str = f"({escala_plantao_str})"
    
    linhas_saida = []
    linhas_saida.append(f"Plantão {data_final_plantao_str} ({escala_final_str})")
    linhas_saida.append(f"📍 Condomínio: {nome_condominio_str}\n")

    if not rondas_pareadas:
        linhas_saida.append("\tNenhuma ronda completa identificada.")
    else:
        for ronda in rondas_pareadas:
            inicio_fmt = ronda["inicio_dt"].strftime("%H:%M")
            if ronda.get("termino_dt"): # Checa se existe termino_dt
                termino_fmt = ronda["termino_dt"].strftime("%H:%M")
            else:
                termino_fmt = "[PENDENTE]"
            linhas_saida.append(f"\tInício: {inicio_fmt:<7}– Término: {termino_fmt:<7}") 

    total_rondas = len(rondas_pareadas) # Usar rondas_pareadas que contém objetos com inicio_dt e termino_dt
    linhas_saida.append(f"\n✅ Total: {total_rondas} rondas no plantão")

    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:")
        linhas_saida.extend(alertas_pareamento)
    
    logger.info(f"Relatório de rondas para {nome_condominio_str} formatado. {total_rondas} rondas, {len(alertas_pareamento)} alertas.")
    return "\n".join(linhas_saida)