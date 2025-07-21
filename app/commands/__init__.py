from .seed import seed_db_command
from .debug import (
    check_ocorrencias_data_command,
    check_rondas_monthly_command,
    debug_ocorrencias_mes_command,
    investigar_discrepancia_junho_2025_command,
    listar_todas_ocorrencias_junho_2025_command,
    investigar_discrepancia_comparativo_command,
    testar_dashboard_ocorrencia_mes_especifico_command,
    testar_filtros_dashboard_ocorrencia_command,
    contar_ocorrencias_30_06_2025_command,
    test_ronda_duplicada_command,
    listar_rondas_condominio_data_command,
    logins_hoje_command,
)
from .relatorios import (
    test_media_dia_trabalhado_command,
    test_media_dias_reais_command,
    test_supervisor_specific_command,
    check_supervisor_working_days_command,
    assign_supervisors_command,
    fix_ocorrencias_definitive_command,
    investigate_rondas_discrepancy_command,
    testar_dashboard_comparativo_command,
)

def register_commands(app):
    app.cli.add_command(seed_db_command)
    app.cli.add_command(check_ocorrencias_data_command)
    app.cli.add_command(check_rondas_monthly_command)
    app.cli.add_command(debug_ocorrencias_mes_command)
    app.cli.add_command(investigar_discrepancia_junho_2025_command)
    app.cli.add_command(listar_todas_ocorrencias_junho_2025_command)
    app.cli.add_command(investigar_discrepancia_comparativo_command)
    app.cli.add_command(testar_dashboard_ocorrencia_mes_especifico_command)
    app.cli.add_command(testar_filtros_dashboard_ocorrencia_command)
    app.cli.add_command(contar_ocorrencias_30_06_2025_command)
    app.cli.add_command(test_ronda_duplicada_command)
    app.cli.add_command(listar_rondas_condominio_data_command)
    app.cli.add_command(test_media_dia_trabalhado_command)
    app.cli.add_command(test_media_dias_reais_command)
    app.cli.add_command(test_supervisor_specific_command)
    app.cli.add_command(check_supervisor_working_days_command)
    app.cli.add_command(assign_supervisors_command)
    app.cli.add_command(fix_ocorrencias_definitive_command)
    app.cli.add_command(investigate_rondas_discrepancy_command)
    app.cli.add_command(testar_dashboard_comparativo_command)
    app.cli.add_command(logins_hoje_command) 