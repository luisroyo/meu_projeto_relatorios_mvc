# report.py
import logging
from datetime import datetime 
from . import config
import re # <--- ADICIONAR ESTA LINHA

logger = logging.getLogger(__name__)

def formatar_relatorio_rondas(nome_condominio: str,
                               data_cabecalho_relatorio: str, 
                               escala_plantao_input_str: str, # Ex: "06-18" ou "18-06" ou None
                               eventos_encontrados: list, 
                               rondas_pareadas: list,
                               alertas_pareamento: list):

    data_final_plantao_str = data_cabecalho_relatorio
    if data_final_plantao_str == config.FALLBACK_DATA_INDEFINIDA:
        logger.warning("Gerando relatório com data de plantão indefinida.")
    
    escala_formatada_str = config.FALLBACK_ESCALA_NAO_INFORMADA
    if escala_plantao_input_str and isinstance(escala_plantao_input_str, str):
        partes_escala = escala_plantao_input_str.strip().split('-')
        if len(partes_escala) == 2:
            try:
                h_inicio = int(partes_escala[0])
                h_fim = int(partes_escala[1])
                escala_formatada_str = f"{h_inicio:02d}h às {h_fim:02d}h"
            except ValueError:
                logger.warning(f"Escala '{escala_plantao_input_str}' com partes não numéricas. Usando como está ou fallback.")
                if escala_plantao_input_str.strip(): # Se não vazio, usa o que foi digitado
                    escala_formatada_str = escala_plantao_input_str.strip()
        elif escala_plantao_input_str.strip(): # Formato não esperado, mas não vazio
            escala_formatada_str = escala_plantao_input_str.strip()


    linhas_saida = [
        f"Plantão {data_final_plantao_str} ({escala_formatada_str})",
        f"Residencial: {nome_condominio}\n"
    ]

    rondas_completas_count = 0
    rondas_exibidas = False
    
    # Ordenar rondas pareadas pelo horário de início para exibição consistente
    # (já devem vir ordenadas do processor, mas uma segurança extra não faz mal)
    rondas_pareadas_ordenadas = sorted(
        [r for r in rondas_pareadas if r.get("inicio_dt")], 
        key=lambda r: r["inicio_dt"]
    )
    # Adicionar rondas órfãs (apenas término) se necessário, talvez no final
    rondas_apenas_termino = [r for r in rondas_pareadas if not r.get("inicio_dt") and r.get("termino_dt")]


    for ronda in rondas_pareadas_ordenadas: # Processa primeiro as que têm início
        if ronda.get("inicio_dt") and isinstance(ronda["inicio_dt"], datetime):
            inicio_fmt = ronda["inicio_dt"].strftime("%H:%M")
            termino_fmt = "[PENDENTE]"
            duracao_str = ""
            if ronda.get("termino_dt") and isinstance(ronda["termino_dt"], datetime):
                termino_fmt = ronda["termino_dt"].strftime("%H:%M")
                if ronda["termino_dt"] > ronda["inicio_dt"]: # Calcula duração se término for após início
                    duracao = ronda["termino_dt"] - ronda["inicio_dt"]
                    total_minutos = int(duracao.total_seconds() / 60)
                    duracao_str = f" ({total_minutos} min)"
                rondas_completas_count += 1
            
            # Adiciona VTR se quiser: (VTR: {ronda['vtr']})
            linhas_saida.append(f"\u2003Início: {inicio_fmt}  – Término: {termino_fmt}{duracao_str}")
            rondas_exibidas = True
    
    # Exibir rondas órfãs (apenas término) se houver e se for desejado
    if rondas_apenas_termino:
        if not rondas_exibidas : linhas_saida.append("") # Espaço se não houve rondas com início
        # linhas_saida.append("\u2003Rondas com apenas término detectado:")
        for ronda_orfã in sorted(rondas_apenas_termino, key=lambda r: r["termino_dt"]):
            termino_fmt = ronda_orfã["termino_dt"].strftime("%H:%M")
            # linhas_saida.append(f"\u2003Início: [N/A] – Término: {termino_fmt} (VTR: {ronda_orfã['vtr']})")
            # Não vamos exibir por padrão para manter a saída limpa como no exemplo,
            # mas os alertas de pareamento já as mencionarão.
            pass


    if not rondas_exibidas and not rondas_apenas_termino : # Se nenhuma ronda (completa ou órfã) foi listada
        if alertas_pareamento:
             linhas_saida.append("\u2003Nenhuma ronda para exibir (verifique observações/alertas).")
        elif eventos_encontrados: # Havia eventos, mas não formaram rondas
             linhas_saida.append("\u2003Nenhuma ronda completa ou parcial para exibir (eventos detectados, mas não formaram rondas).")
        else: # Nenhum evento encontrado
             linhas_saida.append("\u2003Nenhuma ronda para exibir (nenhum evento detectado).")
    
    if rondas_exibidas or rondas_apenas_termino or (eventos_encontrados and not alertas_pareamento and not rondas_pareadas):
        linhas_saida.append(f"\n✅ Total: {rondas_completas_count} rondas completas no plantão")

    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:")
        # Limitar número de alertas ou filtrar por tipo se necessário
        alertas_formatados = []
        for alerta_idx, alerta_msg in enumerate(alertas_pareamento):
            # Tenta extrair a linha original do alerta para dar mais contexto
            match_linha_alerta = re.search(r"\(Linha: '(.*?)'\)", alerta_msg)
            linha_ctx = ""
            if match_linha_alerta:
                linha_ctx = f"  Trecho do Log: \"{match_linha_alerta.group(1)[:100]}...\"" # Limita tamanho

            # Evitar duplicação de "Observações/Alertas" se já estiver na mensagem
            msg_limpa = alerta_msg.replace("Observações/Alertas de Pareamento:", "").strip()
            
            alertas_formatados.append(f"- {msg_limpa}")
            if linha_ctx:
                alertas_formatados.append(linha_ctx)
            if alerta_idx < len(alertas_pareamento) -1 : # Adiciona espaço entre alertas
                 alertas_formatados.append("") 


        linhas_saida.extend(alertas_formatados)


    report_str = "\n".join(linhas_saida)
    return report_str.strip()