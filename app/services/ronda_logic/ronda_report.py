import logging
from datetime import datetime
from . import ronda_config # Ou 'import ronda_config'

logger = logging.getLogger(__name__)

def formatar_relatorio_rondas(nome_condominio: str, data_plantao_manual: str, escala_plantao: str,
                               eventos_encontrados: list, rondas_pareadas: list, alertas_pareamento: list):
    """Formata a string final do relatório de rondas."""
    data_final_plantao_str = ronda_config.FALLBACK_DATA_INDEFINIDA # Usando constante
    if data_plantao_manual:
        try:
            dt_plantao_obj = datetime.strptime(data_plantao_manual.strip(), "%d/%m/%Y")
            data_final_plantao_str = dt_plantao_obj.strftime("%d/%m/%Y")
        except ValueError:
            logger.warning(f"Data de plantão manual ('{data_plantao_manual}') inválida.")
            if eventos_encontrados: 
                data_final_plantao_str = eventos_encontrados[0]["datetime_obj"].strftime("%d/%m/%Y")
    elif eventos_encontrados:
        data_final_plantao_str = eventos_encontrados[0]["datetime_obj"].strftime("%d/%m/%Y")

    escala_final_str = escala_plantao if escala_plantao else ronda_config.FALLBACK_ESCALA_NAO_INFORMADA # Usando constante
    
    linhas_saida = [
        f"Plantão {data_final_plantao_str} ({escala_final_str})",
        "          Projeto Mais com Menos",
        f"\n      📍 Residencial: {nome_condominio}\n"
    ]

    rondas_completas_count = 0
    rondas_exibidas = False
    for ronda in rondas_pareadas: 
        if ronda.get("inicio_dt"):
            inicio_fmt = ronda["inicio_dt"].strftime("%H:%M")
            termino_fmt = ronda["termino_dt"].strftime("%H:%M") if ronda.get("termino_dt") else "[PENDENTE]"
            if ronda.get("termino_dt"): rondas_completas_count += 1
            linhas_saida.append(f"\tInício: {inicio_fmt:<7}– Término: {termino_fmt:<7}") 
            rondas_exibidas = True

    if not rondas_exibidas and not alertas_pareamento:
         linhas_saida.append("\tNenhuma ronda para exibir (verifique alertas).")
    elif not rondas_exibidas and alertas_pareamento:
         linhas_saida.append("\tNenhuma ronda completa para exibir (verifique alertas).")

    linhas_saida.append(f"\n✅ Total: {rondas_completas_count} rondas completas no plantão")

    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:")
        linhas_saida.extend(alertas_pareamento)
    
    return "\n".join(linhas_saida)