import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

from app.services.parada_logic.processor import processar_log_de_paradas

log_bruto = """
[18:41, 05/07/2026] VTR 06: 18:41 inicio de parada
[18:49, 05/07/2026] VTR 06: 18:49 termino de parada
[04:42, 05/07/2026] VTR 04: 04:42 inicio de parada
[04:51, 05/07/2026] VTR 06: 04:51 inicio de parada
[04:56, 05/07/2026] VTR 06: 04:56 termino de parada
[05:00, 05/07/2026] VTR 04: 05:00 termino de parada
"""

relatorio_texto_formatado, total_completas, primeiro_ev_dt, ultimo_ev_dt, soma_duracao_total = processar_log_de_paradas(
    log_bruto_paradas_str=log_bruto,
    nome_condominio_str="LA VIE",
    data_plantao_manual_str="05/07/2026",
    escala_plantao_str="12x36"
)

print(f"Total de paradas encontradas: {total_completas}")
print("Relatorio gerado:")
print(relatorio_texto_formatado)
