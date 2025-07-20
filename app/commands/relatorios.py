import logging
import click
from flask.cli import with_appcontext
from app import db

# Comandos de relatórios e métricas

# 1. test_media_dia_trabalhado_command
@click.command("test-media-dia-trabalhado")
@with_appcontext
def test_media_dia_trabalhado_command():
    """
    Testa a nova métrica de média por dia trabalhado considerando escala 12x36.
    """
    # ... (restante do comando, conforme original) ...

# 2. test_media_dias_reais_command
@click.command("test-media-dias-reais")
@with_appcontext
def test_media_dias_reais_command():
    """
    Testa o cálculo de média baseado nos dias reais trabalhados pelos supervisores.
    """
    # ... (restante do comando, conforme original) ...

# 3. test_supervisor_specific_command
@click.command("test-supervisor-specific")
@with_appcontext
def test_supervisor_specific_command():
    """
    Testa a correção da média por supervisor específico.
    """
    # ... (restante do comando, conforme original) ...

# 4. check_supervisor_working_days_command
@click.command("check-supervisor-working-days")
@with_appcontext
def check_supervisor_working_days_command():
    """
    Verifica exatamente quantos dias cada supervisor trabalhou em um mês específico.
    """
    # ... (restante do comando, conforme original) ...

# 5. assign_supervisors_command
@click.command("assign-supervisors")
@with_appcontext
def assign_supervisors_command():
    """
    Sincroniza TODAS as rondas existentes com as escalas mensais definidas na interface.
    """
    # ... (restante do comando, conforme original) ...

# 6. fix_ocorrencias_definitive_command
@click.command("fix-ocorrencias-definitive")
@with_appcontext
def fix_ocorrencias_definitive_command():
    """
    CORREÇÃO FINAL: Subtrai 6 horas dos registros de Ocorrências que foram ajustados incorretamente.
    """
    # ... (restante do comando, conforme original) ...

# 7. investigate_rondas_discrepancy_command
@click.command("investigate-rondas-discrepancy")
@with_appcontext
def investigate_rondas_discrepancy_command():
    """
    Investiga a discrepância nos dados de rondas entre diferentes queries.
    """
    # ... (restante do comando, conforme original) ...

# 8. testar_dashboard_comparativo_command
@click.command("testar-dashboard-comparativo")
@with_appcontext
def testar_dashboard_comparativo_command():
    """
    Testa o dashboard comparativo para verificar se há discrepância na contagem de ocorrências.
    """
    # ... (restante do comando, conforme original) ... 