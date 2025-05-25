# report.py
import logging
from datetime import datetime
from . import config

logger = logging.getLogger(__name__)

def formatar_relatorio_rondas(nome_condominio: str,
                               data_cabecalho_relatorio: str,
                               escala_plantao_input: str, # Recebe a string original da escala
                               eventos_encontrados: list,
                               rondas_pareadas: list,
                               alertas_pareamento: list):

    data_final_plantao_str = data_cabecalho_relatorio

    # Formatar a string da escala para o formato "HHh às HHh"
    # Assumindo que escala_plantao_input vem como "06-18" ou "18-06"
    if escala_plantao_input == "06-18":
        escala_final_str = "06h às 18h"
    elif escala_plantao_input == "18-06":
        escala_final_str = "18h às 06h"
    elif escala_plantao_input: # Se for outro valor não vazio, usa como está
         escala_final_str = escala_plantao_input
    else: # Se for None ou vazia
        escala_final_str = config.FALLBACK_ESCALA_NAO_INFORMADA # Ou simplesmente string vazia, se preferir

    linhas_saida = [
        f"Plantão {data_final_plantao_str} ({escala_final_str})",
        # REMOVER a linha "Projeto Mais com Menos"
        f"📍 Condomínio: {nome_condominio}\n" # Alterado para "Condomínio" e sem espaços extras antes do emoji
    ]

    rondas_completas_count = 0
    rondas_exibidas = False
    # A ordem das rondas em rondas_pareadas agora deve refletir a ordem de entrada no log,
    # pois não houve reordenação explícita dos eventos_encontrados.
    for ronda in rondas_pareadas:
        if ronda.get("inicio_dt"): # Apenas exibe se houver um início (mesmo que término esteja pendente)
            inicio_fmt = ronda["inicio_dt"].strftime("%H:%M")
            termino_fmt = ronda["termino_dt"].strftime("%H:%M") if ronda.get("termino_dt") else "[PENDENTE]" # Mantém [PENDENTE] se necessário
            if ronda.get("termino_dt"):
                rondas_completas_count += 1
            # Usar U+2003 (EM SPACE) no início e dois espaços normais após os horários
            linhas_saida.append(f"\u2003Início: {inicio_fmt}  – Término: {termino_fmt}  ")
            rondas_exibidas = True
        # Se quiser exibir rondas que SÓ têm término (órfãs), precisaria de um `elif ronda.get("termino_dt"):` aqui.
        # A saída esperada não mostra rondas órfãs, então esta lógica está alinhada.

    if not rondas_exibidas and not alertas_pareamento: # Ajustado para ser mais parecido com o JS (que não exibe nada se não há rondas)
         linhas_saida.append("\u2003Nenhuma ronda para exibir.") # Adiciona indentação
    elif not rondas_exibidas and alertas_pareamento: # Caso haja alertas mas nenhuma ronda completa
         linhas_saida.append("\u2003Nenhuma ronda completa para exibir (verifique alertas).") # Adiciona indentação


    # Remover "completas" da string de total
    linhas_saida.append(f"\n✅ Total: {rondas_completas_count} rondas no plantão")

    # A "saída esperada" não inclui a seção de alertas.
    # Se você quiser OMITIR completamente os alertas para igualar a saída esperada:
    # Comente ou remova o bloco if/extend abaixo.
    # Por enquanto, vou manter, pois é uma funcionalidade informativa do Python.
    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:") # Mantido por enquanto
        linhas_saida.extend(alertas_pareamento)                     # Mantido por enquanto
    
    return "\n".join(linhas_saida)