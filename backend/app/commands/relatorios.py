import logging
import click
from flask.cli import with_appcontext
from app import db
from app.services.dashboard.helpers.kpis import _calculate_supervisor_working_days, _is_supervisor_working_day
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

# Comandos de relatórios e métricas

@click.command("test-media-dia-trabalhado")
@with_appcontext
def test_media_dia_trabalhado_command():
    """
    Testa a nova métrica de média por dia trabalhado considerando escala 12x36.
    """
    try:
        from app.models import User, EscalaMensal
        
        # Busca um supervisor que tenha escala definida
        supervisor = User.query.filter_by(is_supervisor=True, is_approved=True).first()
        if not supervisor:
            click.echo("❌ Nenhum supervisor encontrado no sistema.")
            return
        
        click.echo(f"🔍 Testando métrica para supervisor: {supervisor.username}")
        
        # Define um período de teste (último mês)
        hoje = date.today()
        data_inicio = date(hoje.year, hoje.month, 1)
        if hoje.month == 12:
            data_fim = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        click.echo(f"📅 Período de teste: {data_inicio} a {data_fim}")
        
        # Calcula dias trabalhados
        dias_trabalhados = _calculate_supervisor_working_days(
            supervisor.id, data_inicio, data_fim
        )
        
        click.echo(f"✅ Dias trabalhados pelo supervisor: {dias_trabalhados}")
        
        # Mostra a escala do supervisor
        escalas = EscalaMensal.query.filter_by(
            supervisor_id=supervisor.id,
            ano=hoje.year,
            mes=hoje.month
        ).all()
        
        if escalas:
            click.echo(f"📋 Escala do supervisor para {hoje.month}/{hoje.year}:")
            for escala in escalas:
                click.echo(f"   - {escala.nome_turno}")
        else:
            click.echo(f"⚠️  Supervisor não tem escala definida para {hoje.month}/{hoje.year}")
        
        # Testa alguns dias específicos
        click.echo("\n🧪 Testando alguns dias específicos:")
        for i in range(1, 6):
            data_teste = date(hoje.year, hoje.month, i)
            trabalha = _is_supervisor_working_day(data_teste, {e.nome_turno for e in escalas})
            status = "✅ Trabalha" if trabalha else "❌ Folga"
            click.echo(f"   {data_teste.strftime('%d/%m/%Y')} (dia {'par' if i % 2 == 0 else 'ímpar'}): {status}")
        
        click.echo("\n🎯 Teste concluído com sucesso!")
        
    except Exception as e:
        click.echo(f"❌ Erro durante o teste: {e}")
        logger.error(f"Erro no comando test-media-dia-trabalhado: {e}", exc_info=True)

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

@click.command("check-supervisor-escala")
@with_appcontext
def check_supervisor_escala_command():
    """
    Verifica a escala de um supervisor específico.
    """
    try:
        from app.models import User, EscalaMensal
        
        # Lista todos os supervisores primeiro
        supervisores = User.query.filter_by(is_supervisor=True, is_approved=True).all()
        click.echo("🔍 Supervisores disponíveis no sistema:")
        for sup in supervisores:
            click.echo(f"   - ID: {sup.id}, Username: '{sup.username}'")
        
        # Busca o supervisor Luis especificamente
        supervisor = User.query.filter_by(username="Luis").first()
        if not supervisor:
            # Tenta buscar por username que contenha "Luis"
            supervisor = User.query.filter(User.username.ilike("%Luis%")).first()
            if not supervisor:
                click.echo("\n❌ Supervisor 'Luis' não encontrado no sistema.")
                click.echo("💡 Use um dos IDs listados acima para verificar a escala.")
                return
        
        click.echo(f"\n🔍 Verificando escala para supervisor: {supervisor.username} (ID: {supervisor.id})")
        
        # Define um período de teste (agosto 2025)
        data_inicio = date(2025, 8, 1)
        data_fim = date(2025, 8, 31)
        
        click.echo(f"📅 Período de teste: {data_inicio} a {data_fim}")
        
        # Mostra a escala do supervisor
        escalas = EscalaMensal.query.filter_by(
            supervisor_id=supervisor.id,
            ano=2025,
            mes=8
        ).all()
        
        if escalas:
            click.echo(f"📋 Escala do supervisor para 8/2025:")
            for escala in escalas:
                click.echo(f"   - {escala.nome_turno}")
        else:
            click.echo(f"⚠️  Supervisor não tem escala definida para 8/2025")
            # Verifica se há escalas em outros meses
            escalas_gerais = EscalaMensal.query.filter_by(
                supervisor_id=supervisor.id
            ).all()
            if escalas_gerais:
                click.echo(f"📋 Escalas encontradas em outros períodos:")
                for escala in escalas_gerais:
                    click.echo(f"   - {escala.ano}/{escala.mes}: {escala.nome_turno}")
            else:
                click.echo(f"❌ Supervisor não tem nenhuma escala definida no sistema")
        
        # Testa alguns dias específicos
        click.echo("\n🧪 Testando alguns dias específicos:")
        for i in range(1, 6):
            data_teste = date(2025, 8, i)
            trabalha = _is_supervisor_working_day(data_teste, {e.nome_turno for e in escalas})
            status = "✅ Trabalha" if trabalha else "❌ Folga"
            click.echo(f"   {data_teste.strftime('%d/%m/%Y')} (dia {'par' if i % 2 == 0 else 'ímpar'}): {status}")
        
        # Calcula dias trabalhados
        dias_trabalhados = _calculate_supervisor_working_days(
            supervisor.id, data_inicio, data_fim
        )
        
        click.echo(f"\n✅ Dias trabalhados pelo supervisor: {dias_trabalhados}")
        click.echo(f"📊 Total de dias no período: {(data_fim - data_inicio).days + 1}")
        click.echo(f"🎯 Porcentagem de dias trabalhados: {round((dias_trabalhados / 31) * 100, 1)}%")
        
        click.echo("\n🎯 Verificação concluída!")
        
    except Exception as e:
        click.echo(f"❌ Erro durante a verificação: {e}")
        logger.error(f"Erro no comando check-supervisor-escala: {e}", exc_info=True) 

@click.command("test-dashboard-ocorrencia-supervisor")
@with_appcontext
def test_dashboard_ocorrencia_supervisor_command():
    """
    Testa o dashboard de ocorrências com supervisor específico para verificar a métrica de média por dia trabalhado.
    """
    try:
        from app.services.dashboard.helpers.kpis import _calculate_supervisor_working_days
        from datetime import date
        
        # Define um período de teste (agosto 2025)
        date_start = date(2025, 8, 1)
        date_end = date(2025, 8, 31)
        
        click.echo(f"🧪 Testando cálculo de dias trabalhados para supervisor ID 1 (Luis Royo)")
        click.echo(f"📅 Período: {date_start.strftime('%d/%m/%Y')} a {date_end.strftime('%d/%m/%Y')}")
        
        # Calcula os dias trabalhados
        dias_trabalhados = _calculate_supervisor_working_days(1, date_start, date_end)
        
        click.echo(f"\n📊 Resultados do Cálculo:")
        click.echo(f"   Dias trabalhados pelo supervisor: {dias_trabalhados}")
        click.echo(f"   Total de dias no período: 31")
        
        # Simula o cálculo da média (54 ocorrências ÷ dias trabalhados)
        total_ocorrencias = 54
        media_calculada = round(total_ocorrencias / dias_trabalhados, 2) if dias_trabalhados > 0 else 0
        
        click.echo(f"\n📈 Cálculo da Média:")
        click.echo(f"   Total de ocorrências: {total_ocorrencias}")
        click.echo(f"   Média calculada: {media_calculada}")
        click.echo(f"   Fórmula: {total_ocorrencias} ÷ {dias_trabalhados} = {media_calculada}")
        
        # Verifica se a média está correta
        media_esperada = 3.6  # 54 ÷ 15 = 3.6
        
        if abs(media_calculada - media_esperada) < 0.01:  # Tolerância para diferenças de arredondamento
            click.echo(f"\n✅ SUCESSO! Média calculada corretamente:")
            click.echo(f"   Média atual: {media_calculada}")
            click.echo(f"   Média esperada: {media_esperada}")
            click.echo(f"   Status: ✅ CORRETO")
        else:
            click.echo(f"\n❌ ERRO! Média calculada incorretamente:")
            click.echo(f"   Média atual: {media_calculada}")
            click.echo(f"   Média esperada: {media_esperada}")
            click.echo(f"   Diferença: {abs(media_calculada - media_esperada)}")
            click.echo(f"   Status: ❌ INCORRETO")
        
        click.echo(f"\n🎯 Teste concluído!")
        
    except Exception as e:
        click.echo(f"❌ Erro durante o teste: {e}")
        logger.error(f"Erro no comando test-dashboard-ocorrencia-supervisor: {e}", exc_info=True) 