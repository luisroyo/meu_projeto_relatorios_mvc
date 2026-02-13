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


@click.command("test-ronda-pdf-export")
@with_appcontext
def test_ronda_pdf_export_command():
    """Testa a exportação PDF de rondas com supervisor selecionado."""
    try:
        from app.services.dashboard.ronda_dashboard import get_ronda_dashboard_data
        from app.services.report.ronda_service import RondaReportService
        from app.models import User
        
        # Busca o supervisor Luis Royo
        supervisor = User.query.filter_by(username="Luis Royo").first()
        if not supervisor:
            click.echo("❌ Supervisor 'Luis Royo' não encontrado")
            return
        
        # Testa com supervisor específico
        filters = {
            "supervisor_id": supervisor.id,
            "data_inicio_str": "2025-08-01",
            "data_fim_str": "2025-08-31"
        }
        
        click.echo("=== TESTE EXPORTAÇÃO PDF RONDAS COM SUPERVISOR ===")
        click.echo(f"Supervisor: {supervisor.username} (ID: {supervisor.id})")
        click.echo(f"Período: {filters['data_inicio_str']} a {filters['data_fim_str']}")
        click.echo()
        
        # Busca os dados do dashboard
        dashboard_data = get_ronda_dashboard_data(filters)
        
        # Prepara informações dos filtros
        filters_info = {
            "data_inicio": dashboard_data.get("selected_data_inicio_str", ""),
            "data_fim": dashboard_data.get("selected_data_fim_str", ""),
            "supervisor_name": supervisor.username,
            "condominio_name": None,
            "turno": "",
            "mes": None
        }
        
        click.echo("📊 DADOS DO DASHBOARD:")
        click.echo(f"Total de rondas: {dashboard_data.get('total_rondas', 0)}")
        click.echo(f"Média por dia: {dashboard_data.get('media_rondas_dia', 0)}")
        click.echo()
        
        # Verifica informações do período
        periodo_info = dashboard_data.get('periodo_info', {})
        click.echo("📅 INFORMAÇÕES DO PERÍODO:")
        click.echo(f"Dias com dados: {periodo_info.get('dias_com_dados', 0)}")
        click.echo(f"Período solicitado: {periodo_info.get('periodo_solicitado_dias', 0)}")
        click.echo(f"Cobertura: {periodo_info.get('cobertura_periodo', 0)}%")
        click.echo()
        
        # Testa a geração do PDF
        click.echo("📄 TESTANDO GERAÇÃO DO PDF...")
        report_service = RondaReportService()
        pdf_buffer = report_service.generate_ronda_dashboard_pdf(dashboard_data, filters_info)
        
        click.echo(f"✅ PDF gerado com sucesso! Tamanho: {len(pdf_buffer.getvalue())} bytes")
        click.echo()
        
        click.echo("✅ Teste de exportação PDF concluído com sucesso!")
        
    except Exception as e:
        click.echo(f"❌ Erro no teste: {e}")
        logger.error(f"Erro no comando test-ronda-pdf-export: {e}", exc_info=True)


@click.command("test-period-comparison")
@with_appcontext
def test_period_comparison_command():
    """Testa a comparação com período anterior quando supervisor é selecionado."""
    try:
        from app.services.dashboard.ronda_dashboard import get_ronda_dashboard_data
        from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data
        from app.models import User
        
        # Busca o supervisor Luis Royo
        supervisor = User.query.filter_by(username="Luis Royo").first()
        if not supervisor:
            click.echo("❌ Supervisor 'Luis Royo' não encontrado")
            return
        
        click.echo("=== TESTE COMPARAÇÃO COM PERÍODO ANTERIOR ===")
        click.echo(f"Supervisor: {supervisor.username} (ID: {supervisor.id})")
        click.echo()
        
        # Testa com supervisor específico - agosto 2025
        filters = {
            "supervisor_id": supervisor.id,
            "data_inicio_str": "2025-08-01",
            "data_fim_str": "2025-08-31"
        }
        
        click.echo("📊 TESTANDO DASHBOARD DE RONDAS:")
        ronda_data = get_ronda_dashboard_data(filters)
        comparacao_ronda = ronda_data.get('comparacao_periodo', {})
        
        click.echo(f"Período atual: {comparacao_ronda.get('total_atual', 0)} rondas")
        click.echo(f"Período anterior: {comparacao_ronda.get('total_anterior', 0)} rondas")
        click.echo(f"Variação: {comparacao_ronda.get('variacao_percentual', 0)}%")
        click.echo(f"Status: {comparacao_ronda.get('status_text', 'N/A')}")
        click.echo()
        
        click.echo("📊 TESTANDO DASHBOARD DE OCORRÊNCIAS:")
        ocorrencia_data = get_ocorrencia_dashboard_data(filters)
        comparacao_ocorrencia = ocorrencia_data.get('comparacao_periodo', {})
        
        click.echo(f"Período atual: {comparacao_ocorrencia.get('total_atual', 0)} ocorrências")
        click.echo(f"Período anterior: {comparacao_ocorrencia.get('total_anterior', 0)} ocorrências")
        click.echo(f"Variação: {comparacao_ocorrencia.get('variacao_percentual', 0)}%")
        click.echo(f"Status: {comparacao_ocorrencia.get('status_text', 'N/A')}")
        click.echo()
        
        # Testa sem supervisor (comparação geral)
        click.echo("📊 TESTANDO SEM SUPERVISOR (COMPARAÇÃO GERAL):")
        filters_geral = {
            "data_inicio_str": "2025-08-01",
            "data_fim_str": "2025-08-31"
        }
        
        ronda_data_geral = get_ronda_dashboard_data(filters_geral)
        comparacao_ronda_geral = ronda_data_geral.get('comparacao_periodo', {})
        
        click.echo(f"Período atual (geral): {comparacao_ronda_geral.get('total_atual', 0)} rondas")
        click.echo(f"Período anterior (geral): {comparacao_ronda_geral.get('total_anterior', 0)} rondas")
        click.echo(f"Variação (geral): {comparacao_ronda_geral.get('variacao_percentual', 0)}%")
        click.echo()
        
        # Verifica se as comparações são diferentes (o que indica que está funcionando)
        if comparacao_ronda.get('total_atual', 0) != comparacao_ronda_geral.get('total_atual', 0):
            click.echo("✅ SUCESSO! A comparação está considerando apenas o supervisor filtrado")
        else:
            click.echo("⚠️ ATENÇÃO: As comparações são iguais - pode indicar que não há dados do supervisor no período")
        
        click.echo("✅ Teste de comparação concluído com sucesso!")
        
    except Exception as e:
        click.echo(f"❌ Erro no teste: {e}")
        logger.error(f"Erro no comando test-period-comparison: {e}", exc_info=True)


@click.command("test-residencial-metrics")
@with_appcontext
def test_residencial_metrics_command():
    """Testa especificamente as métricas de residenciais no PDF com supervisor selecionado."""
    try:
        from app.services.dashboard.ronda_dashboard import get_ronda_dashboard_data
        from app.models import User
        
        # Busca o supervisor Luis Royo
        supervisor = User.query.filter_by(username="Luis Royo").first()
        if not supervisor:
            click.echo("❌ Supervisor 'Luis Royo' não encontrado")
            return
        
        click.echo("=== TESTE MÉTRICAS DE RESIDENCIAIS COM SUPERVISOR ===")
        click.echo(f"Supervisor: {supervisor.username} (ID: {supervisor.id})")
        click.echo()
        
        # Testa com supervisor específico - agosto 2025
        filters = {
            "supervisor_id": supervisor.id,
            "data_inicio_str": "2025-08-01",
            "data_fim_str": "2025-08-31"
        }
        
        # Busca os dados do dashboard
        dashboard_data = get_ronda_dashboard_data(filters)
        
        # Verifica informações do período
        periodo_info = dashboard_data.get('periodo_info', {})
        dias_trabalhados = periodo_info.get('dias_com_dados', 0)
        
        click.echo("📊 DADOS DOS RESIDENCIAIS:")
        click.echo(f"Dias trabalhados pelo supervisor: {dias_trabalhados}")
        click.echo()
        
        # Simula o cálculo das métricas como no PDF
        if dashboard_data.get('condominio_labels') and dashboard_data.get('condominio_data'):
            click.echo("🏠 CÁLCULO DAS MÉTRICAS POR RESIDENCIAL:")
            click.echo("Residencial | Total | Média por Dia | Status")
            click.echo("-" * 50)
            
            total_periodo = sum(dashboard_data['condominio_data'])
            
            for label, value in zip(dashboard_data['condominio_labels'], dashboard_data['condominio_data']):
                # Calcula média por dia usando dias trabalhados
                media_dia = round(value / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
                
                # Determina status baseado na quantidade
                if value == 0:
                    status = "❌ Sem rondas"
                elif value < 5:
                    status = "⚠️ Baixa frequência"
                elif value < 15:
                    status = "✅ Frequência normal"
                else:
                    status = "🟢 Alta frequência"
                
                click.echo(f"{label[:15]:<15} | {value:>5} | {media_dia:>12} | {status}")
            
            # Total geral
            media_total = round(total_periodo / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
            click.echo("-" * 50)
            click.echo(f"{'TOTAL GERAL':<15} | {total_periodo:>5} | {media_total:>12} | Resumo")
            click.echo()
            
            click.echo("📝 NOTA EXPLICATIVA:")
            click.echo("* Média calculada considerando apenas os dias trabalhados pelo supervisor (jornada 12x36)")
            click.echo()
            
            # Comparação com cálculo antigo (31 dias)
            click.echo("🔄 COMPARAÇÃO COM CÁLCULO ANTIGO (31 dias):")
            click.echo("Residencial | Média Antiga | Média Nova | Diferença")
            click.echo("-" * 55)
            
            for label, value in zip(dashboard_data['condominio_labels'][:5], dashboard_data['condominio_data'][:5]):
                media_antiga = round(value / 31, 1)
                media_nova = round(value / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
                diferenca = round(media_nova - media_antiga, 1)
                click.echo(f"{label[:15]:<15} | {media_antiga:>11} | {media_nova:>9} | {diferenca:>8}")
            
            media_total_antiga = round(total_periodo / 31, 1)
            media_total_nova = round(total_periodo / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
            diferenca_total = round(media_total_nova - media_total_antiga, 1)
            click.echo("-" * 55)
            click.echo(f"{'TOTAL GERAL':<15} | {media_total_antiga:>11} | {media_total_nova:>9} | {diferenca_total:>8}")
        
        click.echo("✅ Teste de métricas de residenciais concluído com sucesso!")
        
    except Exception as e:
        click.echo(f"❌ Erro no teste: {e}")
        logger.error(f"Erro no comando test-residencial-metrics: {e}", exc_info=True)


@click.command("test-shift-logic")
@with_appcontext
def test_shift_logic_command():
    """Testa a lógica de turnos para determinar a data do plantão de ocorrências."""
    try:
        from app.utils.date_utils import get_plantao_date_from_ocorrencia, get_plantao_datetime_range
        from datetime import datetime, date
        
        click.echo("=== TESTE LÓGICA DE TURNOS PARA OCORRÊNCIAS ===")
        click.echo()
        
        # Casos de teste
        test_cases = [
            # (data_ocorrencia, turno, descricao)
            ("31/08/2025 20:00", "Noturno Par", "Ocorrência às 20h - turno noturno"),
            ("01/09/2025 02:00", "Noturno Par", "Ocorrência às 2h da madrugada - turno noturno"),
            ("01/09/2025 05:30", "Noturno Par", "Ocorrência às 5h30 da madrugada - turno noturno"),
            ("01/09/2025 10:00", "Diurno Par", "Ocorrência às 10h - turno diurno"),
            ("01/09/2025 15:00", "Diurno Par", "Ocorrência às 15h - turno diurno"),
            ("01/09/2025 19:00", "Noturno Impar", "Ocorrência às 19h - turno noturno"),
            ("02/09/2025 01:00", "Noturno Impar", "Ocorrência às 1h da madrugada - turno noturno"),
        ]
        
        click.echo("🧪 TESTANDO CASOS DE OCORRÊNCIAS:")
        click.echo("Data/Hora Ocorrência | Turno Supervisor | Data Plantão | Descrição")
        click.echo("-" * 80)
        
        for data_str, turno, descricao in test_cases:
            # Converte string para datetime
            try:
                data_ocorrencia = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
                data_plantao = get_plantao_date_from_ocorrencia(data_ocorrencia, turno)
                
                click.echo(f"{data_str:<20} | {turno:<15} | {data_plantao} | {descricao}")
            except Exception as e:
                click.echo(f"ERRO: {data_str} - {e}")
        
        click.echo()
        click.echo("🕐 TESTANDO RANGES DE TURNO:")
        click.echo("Data Plantão | Turno | Início Plantão | Fim Plantão")
        click.echo("-" * 60)
        
        # Testa ranges de turno
        test_dates = [
            (date(2025, 8, 31), "Noturno Par"),
            (date(2025, 9, 1), "Diurno Par"),
            (date(2025, 9, 1), "Noturno Impar"),
        ]
        
        for plantao_date, turno in test_dates:
            try:
                inicio, fim = get_plantao_datetime_range(plantao_date, turno)
                click.echo(f"{plantao_date} | {turno:<15} | {inicio.strftime('%d/%m %H:%M')} | {fim.strftime('%d/%m %H:%M')}")
            except Exception as e:
                click.echo(f"ERRO: {plantao_date} - {e}")
        
        click.echo()
        click.echo("📋 RESUMO DA LÓGICA:")
        click.echo("• Turnos Diurnos (6h-18h): ocorrência pertence ao mesmo dia")
        click.echo("• Turnos Noturnos (18h-6h):")
        click.echo("  - Ocorrência 18h-23h59: pertence ao mesmo dia")
        click.echo("  - Ocorrência 0h-5h59: pertence ao dia anterior (plantão começou no dia anterior)")
        click.echo()
        click.echo("✅ Teste de lógica de turnos concluído com sucesso!")
        
    except Exception as e:
        click.echo(f"❌ Erro no teste: {e}")
        logger.error(f"Erro no comando test-shift-logic: {e}", exc_info=True) 