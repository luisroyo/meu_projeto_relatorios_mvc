# report.py
import logging
from datetime import datetime # Embora não usado diretamente, é bom manter se houver manipulação de data futura
from . import config

logger = logging.getLogger(__name__)

def formatar_relatorio_rondas(nome_condominio: str,
                               data_cabecalho_relatorio: str, # Recebe a data já processada (validada ou fallback)
                               escala_plantao_input: str, 
                               eventos_encontrados: list, # Usado para debug ou relatórios mais detalhados, não na saída atual
                               rondas_pareadas: list,
                               alertas_pareamento: list):

    # data_cabecalho_relatorio já vem como string DD/MM/YYYY ou o fallback.
    data_final_plantao_str = data_cabecalho_relatorio
    if data_final_plantao_str == config.FALLBACK_DATA_INDEFINIDA:
        logger.warning("Gerando relatório com data de plantão indefinida.")
        # Pode-se optar por uma mensagem mais explícita no relatório ou manter o fallback.


    escala_final_str = config.FALLBACK_ESCALA_NAO_INFORMADA # Default
    if escala_plantao_input and isinstance(escala_plantao_input, str): # Verifica se é string e não vazia
        escala_limpa = escala_plantao_input.strip()
        if escala_limpa == "06-18":
            escala_final_str = "06h às 18h"
        elif escala_limpa == "18-06":
            escala_final_str = "18h às 06h"
        elif escala_limpa: # Se for outro valor não vazio, usa como está
             escala_final_str = escala_limpa
    # Se escala_plantao_input for None, vazia ou não string, mantém o FALLBACK_ESCALA_NAO_INFORMADA

    linhas_saida = [
        f"Plantão {data_final_plantao_str} ({escala_final_str})",
        f"Residencial: {nome_condominio}\n"
    ]

    rondas_completas_count = 0
    rondas_exibidas = False
    
    for ronda in rondas_pareadas:
        # Apenas processa/exibe rondas que têm um objeto datetime de início válido
        if ronda.get("inicio_dt") and isinstance(ronda["inicio_dt"], datetime):
            inicio_fmt = ronda["inicio_dt"].strftime("%H:%M")
            termino_fmt = "[PENDENTE]"
            if ronda.get("termino_dt") and isinstance(ronda["termino_dt"], datetime):
                termino_fmt = ronda["termino_dt"].strftime("%H:%M")
                rondas_completas_count += 1
            
            linhas_saida.append(f"\u2003Início: {inicio_fmt}  – Término: {termino_fmt}  ")
            rondas_exibidas = True
        elif ronda.get("termino_dt") and isinstance(ronda["termino_dt"], datetime) and not ronda.get("inicio_dt"):
            # Lógica para exibir rondas órfãs (apenas término) se desejado no futuro
            # termino_fmt = ronda["termino_dt"].strftime("%H:%M")
            # linhas_saida.append(f"\u2003Início: [N/A]  – Término: {termino_fmt}  (Alerta: Ronda órfã)")
            # rondas_exibidas = True # Se considerar isso como "exibida"
            pass # Atualmente, não exibe rondas órfãs

    if not rondas_exibidas:
        if alertas_pareamento:
             linhas_saida.append("\u2003Nenhuma ronda completa para exibir (verifique observações/alertas).")
        else:
             linhas_saida.append("\u2003Nenhuma ronda para exibir.")
    
    # Garante que a linha do total só seja adicionada se houver rondas ou alertas a serem considerados.
    # Ou, se preferir, sempre mostrar o total, mesmo que zero.
    if rondas_exibidas or alertas_pareamento or eventos_encontrados : # Mostra total se algo foi processado
        linhas_saida.append(f"\n✅ Total: {rondas_completas_count} rondas no plantão")

    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:")
        linhas_saida.extend(alertas_pareamento)
    elif not rondas_exibidas and not eventos_encontrados: # Se não houve rondas, nem alertas, nem eventos brutos
        # Se a lista estiver apenas com cabeçalho e "nenhuma ronda", pode não querer adicionar mais nada.
        pass


    # Evitar múltiplas linhas em branco no final se não houver alertas
    report_str = "\n".join(linhas_saida)
    return report_str.strip() # Remove espaços/linhas em branco extras do início/fim