import logging
import re
from datetime import datetime

from . import config

logger = logging.getLogger(__name__)


def formatar_relatorio_paradas(
    nome_condominio: str,
    data_cabecalho_relatorio: str,
    escala_plantao_input_str: str,
    eventos_encontrados: list,
    paradas_pareadas: list,
    alertas_pareamento: list,
):

    data_final_plantao_str = data_cabecalho_relatorio
    if data_final_plantao_str == config.FALLBACK_DATA_INDEFINIDA:
        logger.warning("Gerando relatório com data de plantão indefinida.")

    escala_formatada_str = config.FALLBACK_ESCALA_NAO_INFORMADA
    if escala_plantao_input_str and isinstance(escala_plantao_input_str, str):
        partes_escala = escala_plantao_input_str.strip().split("-")
        if len(partes_escala) == 2:
            try:
                h_inicio = int(partes_escala[0])
                h_fim = int(partes_escala[1])
                escala_formatada_str = f"{h_inicio:02d}h às {h_fim:02d}h"
            except ValueError:
                logger.warning(
                    f"Escala '{escala_plantao_input_str}' com partes não numéricas. Usando como está ou fallback."
                )
                if (
                    escala_plantao_input_str.strip()
                ):
                    escala_formatada_str = escala_plantao_input_str.strip()
        elif escala_plantao_input_str.strip():
            escala_formatada_str = escala_plantao_input_str.strip()

    linhas_saida = [
        f"Plantão {data_final_plantao_str} ({escala_formatada_str})",
        f"Residencial: {nome_condominio}\n",
    ]

    paradas_completas_count = 0
    paradas_exibidas = False

    paradas_pareadas_ordenadas = sorted(
        [r for r in paradas_pareadas if r.get("inicio_dt")], key=lambda r: r["inicio_dt"]
    )
    paradas_apenas_termino = [
        r for r in paradas_pareadas if not r.get("inicio_dt") and r.get("termino_dt")
    ]

    for parada in paradas_pareadas_ordenadas:
        if parada.get("inicio_dt") and isinstance(parada["inicio_dt"], datetime):
            inicio_fmt = parada["inicio_dt"].strftime("%H:%M")
            termino_fmt = "[PENDENTE]"
            duracao_str = ""
            if parada.get("termino_dt") and isinstance(parada["termino_dt"], datetime):
                termino_fmt = parada["termino_dt"].strftime("%H:%M")
                if (
                    parada["termino_dt"] > parada["inicio_dt"]
                ):
                    duracao = parada["termino_dt"] - parada["inicio_dt"]
                    total_minutos = int(duracao.total_seconds() / 60)
                    duracao_str = f" ({total_minutos} min)"
                paradas_completas_count += 1

            linhas_saida.append(
                f"\u2003Início: {inicio_fmt}  – Término: {termino_fmt}{duracao_str}"
            )
            paradas_exibidas = True

    if paradas_apenas_termino:
        if not paradas_exibidas:
            linhas_saida.append("")

    if (
        not paradas_exibidas and not paradas_apenas_termino
    ):
        if alertas_pareamento:
            linhas_saida.append(
                "\u2003Nenhuma parada para exibir (verifique observações/alertas)."
            )
        elif eventos_encontrados:
            linhas_saida.append(
                "\u2003Nenhuma parada completa ou parcial para exibir (eventos detectados, mas não formaram paradas)."
            )
        else:
            linhas_saida.append(
                "\u2003Nenhuma parada para exibir (nenhum evento detectado)."
            )

    if (
        paradas_exibidas
        or paradas_apenas_termino
        or (eventos_encontrados and not alertas_pareamento and not paradas_pareadas)
    ):
        linhas_saida.append(
            f"\n✅ Total: {paradas_completas_count} paradas completas no plantão"
        )

    if alertas_pareamento:
        linhas_saida.append("\n\nObservações/Alertas de Pareamento:")
        alertas_formatados = []
        for alerta_idx, alerta_msg in enumerate(alertas_pareamento):
            match_linha_alerta = re.search(r"\(Linha: '(.*?)'\)", alerta_msg)
            linha_ctx = ""
            if match_linha_alerta:
                linha_ctx = f'  Trecho do Log: "{match_linha_alerta.group(1)[:100]}..."'

            msg_limpa = alerta_msg.replace(
                "Observações/Alertas de Pareamento:", ""
            ).strip()

            alertas_formatados.append(f"- {msg_limpa}")
            if linha_ctx:
                alertas_formatados.append(linha_ctx)
            if (
                alerta_idx < len(alertas_pareamento) - 1
            ):
                alertas_formatados.append("")

        linhas_saida.extend(alertas_formatados)

    report_str = "\n".join(linhas_saida)
    return report_str.strip()
