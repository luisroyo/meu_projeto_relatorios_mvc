# Funções utilitárias para lógica de plantão e formatação de relatório de rondas
from datetime import datetime, time
from collections import defaultdict


def identificar_plantao(hora_primeira_ronda: time) -> str:
    """
    Retorna o período do plantão com base na hora da primeira ronda.
    - 06:00 a 17:59 => '06 às 18'
    - 18:00 a 05:59 => '18 às 06'
    """
    if time(6, 0) <= hora_primeira_ronda < time(18, 0):
        return "06 às 18"
    return "18 às 06"


def agrupar_rondas_por_condominio_e_plantao(rondas):
    """
    Agrupa rondas por (condominio_id, data_plantao, plantao).
    Retorna: dict[(condominio_id, data_plantao, plantao)] = [rondas]
    """
    grupos = defaultdict(list)
    for r in rondas:
        plantao = identificar_plantao(r.hora_entrada)
        chave = (r.condominio_id, r.data_plantao, plantao)
        grupos[chave].append(r)
    return grupos


def gerar_relatorio_formatado(grupo_rondas, nome_condominio, data_plantao, plantao):
    """
    Gera relatório formatado conforme modelo do prompt.
    """
    linhas = [
        f"Plantão {data_plantao.strftime('%d/%m/%Y')} ({plantao}h)",
        f"Residencial: {nome_condominio}",
        "",
    ]
    total = 0
    for r in sorted(grupo_rondas, key=lambda x: x.hora_entrada):
        if r.hora_entrada and r.hora_saida:
            duracao = (
                r.duracao_formatada
                if hasattr(r, "duracao_formatada")
                else f"{r.duracao_minutos} min"
            )
            linhas.append(
                f"\tInício: {r.hora_entrada.strftime('%H:%M')}  – Término: {r.hora_saida.strftime('%H:%M')} ({duracao})"
            )
            total += 1
    linhas.append("")
    linhas.append(f"✅ Total: {total} rondas completas no plantão")
    return "\n".join(linhas)
