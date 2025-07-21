import logging
import click
from flask.cli import with_appcontext
from app import db

# Comandos de debug e inspeção

# 1. check_ocorrencias_data_command
@click.command("check-ocorrencias-data")
@with_appcontext
def check_ocorrencias_data_command():
    """
    Verifica os dados de ocorrências no banco de dados para debug do dashboard.
    """
    from app.models import Ocorrencia
    logger = logging.getLogger(__name__)
    click.echo("--- VERIFICAÇÃO DE DADOS DE OCORRÊNCIAS ---")
    total_ocorrencias = Ocorrencia.query.count()
    click.echo(f"Total de ocorrências no banco: {total_ocorrencias}")
    if total_ocorrencias == 0:
        click.echo("❌ NENHUMA OCORRÊNCIA ENCONTRADA NO BANCO DE DADOS!")
        click.echo("Este é o motivo pelo qual o gráfico de evolução diária não aparece.")
        return
    ocorrencias_exemplo = Ocorrencia.query.order_by(Ocorrencia.data_hora_ocorrencia.desc()).limit(5).all()
    click.echo(f"\nÚltimas 5 ocorrências:")
    for oc in ocorrencias_exemplo:
        click.echo(f"  ID: {oc.id}, Data: {oc.data_hora_ocorrencia}, Status: {oc.status}")
    from datetime import datetime, timezone, timedelta
    hoje = datetime.now(timezone.utc)
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ocorrencias_mes_atual = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= primeiro_dia_mes
    ).count()
    click.echo(f"\nOcorrências no mês atual ({hoje.strftime('%B/%Y')}): {ocorrencias_mes_atual}")
    sete_dias_atras = hoje - timedelta(days=7)
    ocorrencias_ultimos_7_dias = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= sete_dias_atras
    ).order_by(Ocorrencia.data_hora_ocorrencia.desc()).all()
    click.echo(f"\nOcorrências nos últimos 7 dias: {len(ocorrencias_ultimos_7_dias)}")
    for oc in ocorrencias_ultimos_7_dias:
        click.echo(f"  {oc.data_hora_ocorrencia.strftime('%d/%m/%Y %H:%M')} - {oc.status}")

# 2. check_rondas_monthly_command
@click.command("check-rondas-monthly")
@with_appcontext
def check_rondas_monthly_command():
    """
    Verifica os dados reais de rondas por mês para debug do dashboard comparativo.
    """
    from app.models import Ronda
    from sqlalchemy import func
    from datetime import datetime
    logger = logging.getLogger(__name__)
    click.echo("--- VERIFICAÇÃO DE DADOS REAIS DE RONDAS POR MÊS ---")
    current_year = datetime.now().year
    click.echo(f"Ano atual: {current_year}")
    query_result = (
        db.session.query(
            func.to_char(Ronda.data_plantao_ronda, "YYYY-MM").label("mes"),
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total")
        )
        .filter(func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year))
        .group_by(func.to_char(Ronda.data_plantao_ronda, "YYYY-MM"))
        .order_by(func.to_char(Ronda.data_plantao_ronda, "YYYY-MM"))
        .all()
    )
    click.echo(f"\nDados reais de rondas por mês ({current_year}):")
    for mes, total in query_result:
        click.echo(f"  {mes}: {total} rondas")
    total_geral = sum(total for _, total in query_result)
    click.echo(f"\nTotal geral: {total_geral} rondas")
    rondas_sem_data = Ronda.query.filter(Ronda.data_plantao_ronda.is_(None)).count()
    if rondas_sem_data > 0:
        click.echo(f"⚠️  ATENÇÃO: {rondas_sem_data} rondas sem data_plantao_ronda!")
    query_result_alt = (
        db.session.query(
            func.to_char(Ronda.data_hora_inicio, "YYYY-MM").label("mes"),
            func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total")
        )
        .filter(func.to_char(Ronda.data_hora_inicio, "YYYY") == str(current_year))
        .group_by(func.to_char(Ronda.data_hora_inicio, "YYYY-MM"))
        .order_by(func.to_char(Ronda.data_hora_inicio, "YYYY-MM"))
        .all()
    )
    click.echo(f"\nDados alternativos (por data_hora_inicio):")
    for mes, total in query_result_alt:
        click.echo(f"  {mes}: {total} rondas")
    total_geral_alt = sum(total for _, total in query_result_alt)
    click.echo(f"Total geral (alt): {total_geral_alt} rondas")

# 3. debug_ocorrencias_mes_command
@click.command("debug-ocorrencias-mes")
@click.option('--ano', default=2025, help='Ano para filtrar (default: 2025)')
@click.option('--mes', default=6, help='Mês para filtrar (default: 6 - junho)')
@with_appcontext
def debug_ocorrencias_mes_command(ano, mes):
    """
    Executa queries de debug para ocorrências de um mês específico.
    Lista todas as ocorrências do mês, dias distintos, e verifica se há ocorrências de outros meses sendo incluídas.
    """
    from app.models import Ocorrencia
    from sqlalchemy import extract, func
    from datetime import date, timedelta
    click.echo(f"--- DEBUG OCORRÊNCIAS PARA {mes:02d}/{ano} ---")
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim = date(ano, mes + 1, 1) - timedelta(days=1)
    ocorrencias = (
        Ocorrencia.query
        .filter(Ocorrencia.data_hora_ocorrencia >= data_inicio)
        .filter(Ocorrencia.data_hora_ocorrencia <= data_fim)
        .order_by(Ocorrencia.data_hora_ocorrencia)
        .all()
    )
    click.echo(f"Total de ocorrências entre {data_inicio} e {data_fim}: {len(ocorrencias)}")
    for o in ocorrencias:
        click.echo(f"  ID: {o.id} | Data: {o.data_hora_ocorrencia} | Status: {o.status}")
    dias_distintos = (
        Ocorrencia.query
        .with_entities(func.date(Ocorrencia.data_hora_ocorrencia))
        .filter(Ocorrencia.data_hora_ocorrencia >= data_inicio)
        .filter(Ocorrencia.data_hora_ocorrencia <= data_fim)
        .group_by(func.date(Ocorrencia.data_hora_ocorrencia))
        .order_by(func.date(Ocorrencia.data_hora_ocorrencia))
        .all()
    )
    click.echo(f"Dias distintos com ocorrências em {mes:02d}/{ano}: {len(dias_distintos)}")
    for d in dias_distintos:
        click.echo(f"  Dia: {d[0]}")
    ocorrencias_julho = (
        Ocorrencia.query
        .filter(Ocorrencia.data_hora_ocorrencia > data_fim)
        .order_by(Ocorrencia.data_hora_ocorrencia)
        .limit(20)
        .all()
    )
    click.echo(f"Ocorrências após {data_fim} (primeiros 20 registros): {len(ocorrencias_julho)}")
    for o in ocorrencias_julho:
        click.echo(f"  ID: {o.id} | Data: {o.data_hora_ocorrencia} | Status: {o.status}")
    click.echo("--- FIM DO DEBUG ---")

# 4. investigar_discrepancia_junho_2025_command
@click.command("investigar-discrepancia-junho-2025")
@with_appcontext
def investigar_discrepancia_junho_2025_command():
    """
    Investiga a discrepância entre as ocorrências contadas e o total real no banco.
    Verifica diferentes filtros e condições que podem estar causando a diferença.
    """
    from datetime import datetime, timezone
    from app.models import Ocorrencia, OcorrenciaTipo
    from sqlalchemy import func
    logger = logging.getLogger(__name__)
    click.echo("=== INVESTIGAÇÃO DE DISCREPÂNCIA - JUNHO DE 2025 ===")
    inicio_junho = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    fim_junho = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    click.echo(f"\n📊 ANÁLISE GERAL:")
    click.echo(f"   Período analisado: 01/06/2025 a 30/06/2025")
    click.echo(f"   Início UTC: {inicio_junho}")
    click.echo(f"   Fim UTC: {fim_junho}")
    total_geral = Ocorrencia.query.count()
    click.echo(f"\n🔍 TOTAL GERAL NO BANCO:")
    click.echo(f"   Total de ocorrências no banco: {total_geral}")
    ocorrencias_sem_data = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia.is_(None)
    ).count()
    click.echo(f"\n⚠️ OCORRÊNCIAS SEM DATA:")
    click.echo(f"   Ocorrências com data_hora_ocorrencia NULL: {ocorrencias_sem_data}")
    if ocorrencias_sem_data > 0:
        click.echo(f"   IDs das ocorrências sem data:")
        ocorrencias_sem_data_list = Ocorrencia.query.filter(
            Ocorrencia.data_hora_ocorrencia.is_(None)
        ).all()
        for oc in ocorrencias_sem_data_list:
            click.echo(f"     - ID: {oc.id}, Status: {oc.status}, Data Criação: {oc.data_criacao}")
    ocorrencias_periodo = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_junho,
        Ocorrencia.data_hora_ocorrencia < fim_junho
    ).count()
    click.echo(f"\n📅 OCORRÊNCIAS NO PERÍODO (FILTRO PRINCIPAL):")
    click.echo(f"   Ocorrências em junho/2025: {ocorrencias_periodo}")
    ocorrencias_antes = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia < inicio_junho
    ).count()
    click.echo(f"\n📅 OCORRÊNCIAS ANTES DO PERÍODO:")
    click.echo(f"   Ocorrências antes de 01/06/2025: {ocorrencias_antes}")
    ocorrencias_depois = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= fim_junho
    ).count()
    click.echo(f"\n📅 OCORRÊNCIAS APÓS O PERÍODO:")
    click.echo(f"   Ocorrências após 30/06/2025: {ocorrencias_depois}")
    total_calculado = ocorrencias_periodo + ocorrencias_antes + ocorrencias_depois + ocorrencias_sem_data
    click.echo(f"\n🧮 VERIFICAÇÃO MATEMÁTICA:")
    click.echo(f"   Período + Antes + Depois + Sem Data = {ocorrencias_periodo} + {ocorrencias_antes} + {ocorrencias_depois} + {ocorrencias_sem_data} = {total_calculado}")
    click.echo(f"   Total real no banco: {total_geral}")
    click.echo(f"   Diferença: {total_geral - total_calculado}")
    status_analysis = (
        db.session.query(
            Ocorrencia.status,
            func.count(Ocorrencia.id).label('quantidade')
        )
        .filter(
            Ocorrencia.data_hora_ocorrencia >= inicio_junho,
            Ocorrencia.data_hora_ocorrencia < fim_junho
        )
        .group_by(Ocorrencia.status)
        .all()
    )
    click.echo(f"\n📈 ANÁLISE POR STATUS NO PERÍODO:")
    for status, quantidade in status_analysis:
        click.echo(f"   • {status}: {quantidade}")
    click.echo(f"\n🔍 OCORRÊNCIAS COM DATAS ESTRANHAS:")
    ocorrencias_antigas = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia < datetime(2020, 1, 1, tzinfo=timezone.utc)
    ).count()
    click.echo(f"   Ocorrências antes de 2020: {ocorrencias_antigas}")
    ocorrencias_futuras = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia > datetime.now(timezone.utc)
    ).count()
    click.echo(f"   Ocorrências no futuro: {ocorrencias_futuras}")
    click.echo(f"\n🔍 COMPARAÇÃO DATA_CRIACAO vs DATA_HORA_OCORRENCIA:")
    ocorrencias_criadas_junho = Ocorrencia.query.filter(
        Ocorrencia.data_criacao >= inicio_junho,
        Ocorrencia.data_criacao < fim_junho
    ).count()
    click.echo(f"   Ocorrências CRIADAS em junho/2025: {ocorrencias_criadas_junho}")
    ocorrencias_ocorridas_junho = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_junho,
        Ocorrencia.data_hora_ocorrencia < fim_junho
    ).count()
    click.echo(f"   Ocorrências OCORRIDAS em junho/2025: {ocorrencias_ocorridas_junho}")
    click.echo(f"\n🔍 VERIFICAÇÃO DE PROBLEMAS:")
    ids_duplicados = db.session.query(Ocorrencia.id).group_by(Ocorrencia.id).having(
        func.count(Ocorrencia.id) > 1
    ).all()
    click.echo(f"   IDs duplicados: {len(ids_duplicados)}")
    click.echo(f"\n✅ RESUMO DA INVESTIGAÇÃO:")
    click.echo(f"   • Total no banco: {total_geral}")
    click.echo(f"   • Ocorrências em junho/2025: {ocorrencias_periodo}")
    click.echo(f"   • Ocorrências sem data: {ocorrencias_sem_data}")
    click.echo(f"   • Ocorrências criadas em junho: {ocorrencias_criadas_junho}")
    click.echo(f"   • Ocorrências ocorridas em junho: {ocorrencias_ocorridas_junho}")
    if ocorrencias_periodo != 188:
        click.echo(f"\n❌ PROBLEMA IDENTIFICADO:")
        click.echo(f"   Esperado: 188 ocorrências")
        click.echo(f"   Encontrado: {ocorrencias_periodo} ocorrências")
        click.echo(f"   Diferença: {188 - ocorrencias_periodo}")
        if ocorrencias_sem_data > 0:
            click.echo(f"   ⚠️ Possível causa: {ocorrencias_sem_data} ocorrências sem data_hora_ocorrencia")
        if ocorrencias_criadas_junho != ocorrencias_periodo:
            click.echo(f"   ⚠️ Possível causa: diferença entre data de criação e data da ocorrência")
    logger.info(f"Investigação de discrepância concluída. Período: {ocorrencias_periodo}, Total: {total_geral}")

# 5. listar_todas_ocorrencias_junho_2025_command
@click.command("listar-todas-ocorrencias-junho-2025")
@with_appcontext
def listar_todas_ocorrencias_junho_2025_command():
    """
    Lista todas as 188 ocorrências de junho de 2025 com detalhes completos.
    Ajuda a identificar quais podem estar sendo excluídas da métrica.
    """
    from datetime import datetime, timezone
    from app.models import Ocorrencia, OcorrenciaTipo, Condominio, User
    logger = logging.getLogger(__name__)
    click.echo("=== LISTA COMPLETA - OCORRÊNCIAS JUNHO 2025 ===")
    inicio_junho = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    fim_junho = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    from sqlalchemy.orm import aliased
    Supervisor = aliased(User)
    ocorrencias = (
        Ocorrencia.query
        .join(OcorrenciaTipo, Ocorrencia.ocorrencia_tipo_id == OcorrenciaTipo.id)
        .outerjoin(Condominio, Ocorrencia.condominio_id == Condominio.id)
        .join(User, Ocorrencia.registrado_por_user_id == User.id)
        .outerjoin(Supervisor, Ocorrencia.supervisor_id == Supervisor.id)
        .filter(
            Ocorrencia.data_hora_ocorrencia >= inicio_junho,
            Ocorrencia.data_hora_ocorrencia < fim_junho
        )
        .order_by(Ocorrencia.data_hora_ocorrencia)
        .all()
    )
    total_ocorrencias = len(ocorrencias)
    click.echo(f"\n📊 TOTAL ENCONTRADO: {total_ocorrencias} ocorrências")
    if total_ocorrencias == 0:
        click.echo("❌ Nenhuma ocorrência encontrada!")
        return
    condominios_count = {}
    tipos_count = {}
    status_count = {}
    users_count = {}
    click.echo(f"\n📝 LISTA DETALHADA:")
    click.echo("=" * 120)
    for i, oc in enumerate(ocorrencias, 1):
        data_formatada = oc.data_hora_ocorrencia.strftime('%d/%m/%Y %H:%M')
        data_criacao_formatada = oc.data_criacao.strftime('%d/%m/%Y %H:%M') if oc.data_criacao else "N/A"
        condominio_nome = oc.condominio.nome if oc.condominio else "Sem condomínio"
        tipo_nome = oc.tipo.nome if oc.tipo else "Sem tipo"
        registrado_por = oc.registrado_por.username if oc.registrado_por else "N/A"
        supervisor = oc.supervisor.username if oc.supervisor else "N/A"
        condominios_count[condominio_nome] = condominios_count.get(condominio_nome, 0) + 1
        tipos_count[tipo_nome] = tipos_count.get(tipo_nome, 0) + 1
        status_count[oc.status] = status_count.get(oc.status, 0) + 1
        users_count[registrado_por] = users_count.get(registrado_por, 0) + 1
        click.echo(f"\n{i:3d}. OCORRÊNCIA #{oc.id}")
        click.echo(f"    📅 Data Ocorrência: {data_formatada}")
        click.echo(f"    📅 Data Criação: {data_criacao_formatada}")
        click.echo(f"    🏢 Condomínio: {condominio_nome}")
        click.echo(f"    📋 Tipo: {tipo_nome}")
        click.echo(f"    🔄 Status: {oc.status}")
        click.echo(f"    👤 Registrado por: {registrado_por}")
        click.echo(f"    👨‍💼 Supervisor: {supervisor}")
        if oc.turno:
            click.echo(f"    ⏰ Turno: {oc.turno}")
        if oc.endereco_especifico:
            click.echo(f"    📍 Endereço: {oc.endereco_especifico}")
        if oc.orgaos_acionados:
            orgaos = [org.nome for org in oc.orgaos_acionados]
            click.echo(f"    🏛️ Órgãos: {', '.join(orgaos)}")
        if oc.colaboradores_envolvidos:
            colaboradores = [col.nome_completo for col in oc.colaboradores_envolvidos]
            click.echo(f"    👥 Colaboradores: {', '.join(colaboradores)}")
        click.echo("-" * 80)
    click.echo(f"\n📊 ANÁLISE ESTATÍSTICA:")
    click.echo(f"   Total de ocorrências: {total_ocorrencias}")
    click.echo(f"\n🏢 POR CONDOMÍNIO:")
    for cond, count in sorted(condominios_count.items(), key=lambda x: x[1], reverse=True):
        percentual = (count / total_ocorrencias) * 100
        click.echo(f"   • {cond}: {count} ({percentual:.1f}%)")
    click.echo(f"\n📋 POR TIPO:")
    for tipo, count in sorted(tipos_count.items(), key=lambda x: x[1], reverse=True):
        percentual = (count / total_ocorrencias) * 100
        click.echo(f"   • {tipo}: {count} ({percentual:.1f}%)")
    click.echo(f"\n🔄 POR STATUS:")
    for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
        percentual = (count / total_ocorrencias) * 100
        click.echo(f"   • {status}: {count} ({percentual:.1f}%)")
    click.echo(f"\n👤 POR USUÁRIO:")
    for user, count in sorted(users_count.items(), key=lambda x: x[1], reverse=True):
        percentual = (count / total_ocorrencias) * 100
        click.echo(f"   • {user}: {count} ({percentual:.1f}%)")
    ocorrencias_sem_condominio = sum(1 for oc in ocorrencias if not oc.condominio)
    if ocorrencias_sem_condominio > 0:
        click.echo(f"   ⚠️ {ocorrencias_sem_condominio} ocorrências sem condomínio")
    ocorrencias_sem_supervisor = sum(1 for oc in ocorrencias if not oc.supervisor)
    if ocorrencias_sem_supervisor > 0:
        click.echo(f"   ⚠️ {ocorrencias_sem_supervisor} ocorrências sem supervisor")
    ocorrencias_sem_turno = sum(1 for oc in ocorrencias if not oc.turno)
    if ocorrencias_sem_turno > 0:
        click.echo(f"   ⚠️ {ocorrencias_sem_turno} ocorrências sem turno")
    ocorrencias_com_endereco = sum(1 for oc in ocorrencias if oc.endereco_especifico)
    click.echo(f"   📍 {ocorrencias_com_endereco} ocorrências com endereço específico")
    ocorrencias_com_orgaos = sum(1 for oc in ocorrencias if oc.orgaos_acionados)
    click.echo(f"   🏛️ {ocorrencias_com_orgaos} ocorrências com órgãos acionados")
    ocorrencias_com_colaboradores = sum(1 for oc in ocorrencias if oc.colaboradores_envolvidos)
    click.echo(f"   👥 {ocorrencias_com_colaboradores} ocorrências com colaboradores")
    click.echo(f"\n✅ INVESTIGAÇÃO CONCLUÍDA!")
    click.echo(f"   Compare esta lista com a métrica que mostra 184 ocorrências")
    click.echo(f"   para identificar quais 4 estão sendo excluídas.")
    logger.info(f"Listagem completa de ocorrências de junho concluída. Total: {total_ocorrencias}")

# 6. investigar_discrepancia_comparativo_command
@click.command("investigar-discrepancia-comparativo")
@with_appcontext
def investigar_discrepancia_comparativo_command():
    """
    Investiga especificamente a discrepância entre os modos do dashboard comparativo.
    """
    from datetime import datetime, timedelta, date
    from app.models import Ocorrencia
    from app.services.dashboard.comparativo.processor import DataProcessor
    from app.services.dashboard.comparativo.aggregator import DataAggregator
    from app.services.dashboard.comparativo.filters import FilterApplier
    from sqlalchemy import func
    logger = logging.getLogger(__name__)
    click.echo("=== INVESTIGAÇÃO DA DISCREPÂNCIA NO DASHBOARD COMPARATIVO ===")
    filters = {}
    year = 2025
    month = 6
    click.echo(f"\n🔍 COMPARAÇÃO DOS DOIS MODOS:")
    click.echo(f"\n📊 MODO 1: TODOS OS MESES")
    try:
        rondas_all, ocorrencias_all = DataProcessor.process_all_months_mode(year, filters)
        click.echo(f"   Ocorrências em junho (índice 5): {ocorrencias_all[5]}")
    except Exception as e:
        click.echo(f"   ❌ Erro: {e}")
    click.echo(f"\n📊 MODO 2: MÊS ÚNICO")
    try:
        rondas_single, ocorrencias_single = DataProcessor.process_single_month_mode(year, month, filters)
        click.echo(f"   Ocorrências em junho (índice 5): {ocorrencias_single[5]}")
    except Exception as e:
        click.echo(f"   ❌ Erro: {e}")
    diferenca = ocorrencias_all[5] - ocorrencias_single[5]
    click.echo(f"\n📊 DIFERENÇA: {diferenca} ocorrências")
    click.echo(f"\n🔍 INVESTIGANDO O PROBLEMA:")
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    click.echo(f"   Data início (mês único): {start_date}")
    click.echo(f"   Data fim (mês único): {end_date}")
    temp_filters = filters.copy()
    temp_filters["data_inicio_str"] = start_date.strftime("%Y-%m-%d")
    temp_filters["data_fim_str"] = end_date.strftime("%Y-%m-%d")
    click.echo(f"   Filtros temporários: {temp_filters}")
    click.echo(f"\n📊 TESTE DO AGREGADOR COM FILTROS DO MÊS ÚNICO:")
    try:
        ocorrencias_raw_single = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, temp_filters, is_ronda=False
        )
        click.echo(f"   Dados brutos: {ocorrencias_raw_single}")
        junho_single = None
        for mes_str, total in ocorrencias_raw_single:
            if mes_str == "2025-06":
                junho_single = total
                break
        click.echo(f"   Ocorrências em junho (agregador com filtros): {junho_single}")
    except Exception as e:
        click.echo(f"   ❌ Erro no agregador: {e}")
    click.echo(f"\n📊 TESTE DO AGREGADOR SEM FILTROS:")
    try:
        ocorrencias_raw_all = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, filters, is_ronda=False
        )
        click.echo(f"   Dados brutos: {ocorrencias_raw_all}")
        junho_all = None
        for mes_str, total in ocorrencias_raw_all:
            if mes_str == "2025-06":
                junho_all = total
                break
        click.echo(f"   Ocorrências em junho (agregador sem filtros): {junho_all}")
    except Exception as e:
        click.echo(f"   ❌ Erro no agregador: {e}")
    click.echo(f"\n🔍 VERIFICAÇÃO DOS FILTROS:")
    query_sem_filtros = db.session.query(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
        func.count(Ocorrencia.id)
    ).filter(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year)
    ).group_by(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM")
    ).all()
    click.echo(f"   Query sem filtros: {query_sem_filtros}")
    query_com_filtros = db.session.query(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
        func.count(Ocorrencia.id)
    )
    query_com_filtros = FilterApplier.apply_ocorrencia_filters(query_com_filtros, temp_filters)
    query_com_filtros = query_com_filtros.filter(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year)
    )
    result_com_filtros = (
        query_com_filtros.group_by(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"))
        .order_by(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"))
        .all()
    )
    click.echo(f"   Query com filtros: {result_com_filtros}")
    if diferenca > 0:
        click.echo(f"   Procurando {diferenca} ocorrências que estão sendo excluídas...")
        ocorrencias_junho = Ocorrencia.query.filter(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM") == "2025-06"
        ).all()
        ocorrencias_excluidas = []
        for oc in ocorrencias_junho:
            if oc.data_hora_ocorrencia:
                data_oc = oc.data_hora_ocorrencia.date()
                if data_oc < start_date or data_oc > end_date:
                    ocorrencias_excluidas.append(oc)
        if ocorrencias_excluidas:
            click.echo(f"   Ocorrências excluídas pelos filtros de data: {len(ocorrencias_excluidas)}")
            for oc in ocorrencias_excluidas:
                click.echo(f"     - ID: {oc.id}, Data: {oc.data_hora_ocorrencia}")
        else:
            click.echo(f"   Nenhuma ocorrência excluída pelos filtros de data")
    click.echo(f"\n✅ RESUMO DA INVESTIGAÇÃO:")
    click.echo(f"   • Modo 'todos os meses': {ocorrencias_all[5]} ocorrências")
    click.echo(f"   • Modo 'mês único': {ocorrencias_single[5]} ocorrências")
    click.echo(f"   • Diferença: {diferenca} ocorrências")
    if diferenca > 0:
        click.echo(f"\n🚨 PROBLEMA IDENTIFICADO:")
        click.echo(f"   O modo 'mês único' está aplicando filtros de data que excluem {diferenca} ocorrências")
        click.echo(f"   Isso pode estar causando a discrepância de 184 vs 188 no dashboard")
    logger.info(f"Investigação da discrepância no comparativo concluída. Diferença: {diferenca}")

# 7. testar_dashboard_ocorrencia_mes_especifico_command
@click.command("testar-dashboard-ocorrencia-mes-especifico")
@with_appcontext
def testar_dashboard_ocorrencia_mes_especifico_command():
    """
    Testa o dashboard de ocorrências quando um mês específico é selecionado.
    """
    from datetime import datetime, timezone, timedelta
    from app.models import Ocorrencia
    from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data
    from app.blueprints.admin.routes_dashboard import _get_date_range_from_month
    from sqlalchemy import func
    logger = logging.getLogger(__name__)
    click.echo("=== TESTE DO DASHBOARD DE OCORRÊNCIAS COM MÊS ESPECÍFICO ===")
    current_year = 2025
    month = 6
    click.echo(f"\n📊 TESTE COM MÊS ESPECÍFICO: {month}/{current_year}")
    click.echo(f"\n🔍 SIMULAÇÃO DO DASHBOARD:")
    start_date_str, end_date_str = _get_date_range_from_month(current_year, month)
    click.echo(f"   Data início (dashboard): {start_date_str}")
    click.echo(f"   Data fim (dashboard): {end_date_str}")
    filters = {
        "condominio_id": None,
        "tipo_id": None,
        "status": "",
        "supervisor_id": None,
        "mes": month,
        "data_inicio_str": start_date_str,
        "data_fim_str": end_date_str,
    }
    click.echo(f"   Filtros aplicados: {filters}")
    click.echo(f"\n📊 TESTE DO DASHBOARD:")
    try:
        dashboard_data = get_ocorrencia_dashboard_data(filters)
        total_dashboard = dashboard_data.get("total_ocorrencias", 0)
        click.echo(f"   Total de ocorrências (dashboard): {total_dashboard}")
    except Exception as e:
        click.echo(f"   ❌ Erro no dashboard: {e}")
        total_dashboard = 0
    click.echo(f"\n🔍 COMPARAÇÃO DIRETA:")
    start_date_dt = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_date_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    click.echo(f"   Data início DT: {start_date_dt}")
    click.echo(f"   Data fim DT: {end_date_dt}")
    total_direto = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= start_date_dt,
        Ocorrencia.data_hora_ocorrencia <= end_date_dt
    ).count()
    click.echo(f"   Total direto: {total_direto}")
    click.echo(f"   Diferença: {total_direto - total_dashboard}")
    click.echo(f"\n📊 TESTE COM FUN.TO_CHAR:")
    total_func_to_char = Ocorrencia.query.filter(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM") == f"{current_year:04d}-{month:02d}"
    ).count()
    click.echo(f"   Total com func.to_char: {total_func_to_char}")
    click.echo(f"\n🔍 VERIFICAÇÃO DE PROCESSAMENTO DE DATAS:")
    from app.utils.date_utils import parse_date_range
    date_start_range, date_end_range = parse_date_range(start_date_str, end_date_str)
    click.echo(f"   Date start range: {date_start_range}")
    click.echo(f"   Date end range: {date_end_range}")
    click.echo(f"   Tipo date_start_range: {type(date_start_range)}")
    click.echo(f"   Tipo date_end_range: {type(date_end_range)}")
    from datetime import time
    date_start_range_dt = datetime.combine(date_start_range, time.min, tzinfo=timezone.utc)
    date_end_range_dt = datetime.combine(date_end_range, time.max, tzinfo=timezone.utc)
    click.echo(f"   Date start range DT: {date_start_range_dt}")
    click.echo(f"   Date end range DT: {date_end_range_dt}")
    total_dashboard_dates = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= date_start_range_dt,
        Ocorrencia.data_hora_ocorrencia <= date_end_range_dt
    ).count()
    click.echo(f"   Total com datas do dashboard: {total_dashboard_dates}")
    if total_direto != total_dashboard:
        click.echo(f"\n🔍 INVESTIGANDO OCORRÊNCIAS EXCLUÍDAS:")
        ocorrencias_excluidas = (
            Ocorrencia.query.filter(
                Ocorrencia.data_hora_ocorrencia >= start_date_dt,
                Ocorrencia.data_hora_ocorrencia <= end_date_dt
            )
            .filter(
                ~Ocorrencia.data_hora_ocorrencia.between(date_start_range_dt, date_end_range_dt)
            )
            .all()
        )
        if ocorrencias_excluidas:
            click.echo(f"   Ocorrências excluídas pelo dashboard: {len(ocorrencias_excluidas)}")
            for oc in ocorrencias_excluidas:
                click.echo(f"     - ID: {oc.id}, Data: {oc.data_hora_ocorrencia}")
        ocorrencias_incluidas_extra = (
            Ocorrencia.query.filter(
                Ocorrencia.data_hora_ocorrencia.between(date_start_range_dt, date_end_range_dt)
            )
            .filter(
                ~Ocorrencia.data_hora_ocorrencia.between(start_date_dt, end_date_dt)
            )
            .all()
        )
        if ocorrencias_incluidas_extra:
            click.echo(f"   Ocorrências incluídas extra pelo dashboard: {len(ocorrencias_incluidas_extra)}")
            for oc in ocorrencias_incluidas_extra:
                click.echo(f"     - ID: {oc.id}, Data: {oc.data_hora_ocorrencia}")
    click.echo(f"\n✅ RESUMO:")
    click.echo(f"   • Total direto: {total_direto}")
    click.echo(f"   • Total dashboard: {total_dashboard}")
    click.echo(f"   • Total func.to_char: {total_func_to_char}")
    click.echo(f"   • Total datas dashboard: {total_dashboard_dates}")
    if total_dashboard != 188:
        click.echo(f"\n❌ PROBLEMA IDENTIFICADO:")
        click.echo(f"   O dashboard está mostrando {total_dashboard} em vez de 188")
        click.echo(f"   Diferença: {188 - total_dashboard} ocorrências")
    logger.info(f"Teste do dashboard com mês específico concluído. Dashboard: {total_dashboard}, Direto: {total_direto}")

# 8. testar_filtros_dashboard_ocorrencia_command
@click.command("testar-filtros-dashboard-ocorrencia")
@with_appcontext
def testar_filtros_dashboard_ocorrencia_command():
    """
    Testa os mesmos filtros usados pelo dashboard de ocorrências para identificar a discrepância.
    Simula exatamente o que o dashboard faz.
    """
    from datetime import datetime, timezone, time
    from app.models import Ocorrencia
    from app.services import ocorrencia_service
    from app.utils.date_utils import parse_date_range
    from sqlalchemy import func
    logger = logging.getLogger(__name__)
    click.echo("=== TESTE DOS FILTROS DO DASHBOARD DE OCORRÊNCIAS ===")
    filters = {
        "condominio_id": None,
        "tipo_id": None,
        "status": "",
        "supervisor_id": None,
        "mes": 6,
        "data_inicio_str": "2025-06-01",
        "data_fim_str": "2025-06-30",
    }
    click.echo(f"\n📊 FILTROS APLICADOS:")
    click.echo(f"   Filtros: {filters}")
    data_inicio_str = filters.get("data_inicio_str")
    data_fim_str = filters.get("data_fim_str")
    date_start_range, date_end_range = parse_date_range(data_inicio_str, data_fim_str)
    click.echo(f"\n📅 PROCESSAMENTO DE DATAS:")
    click.echo(f"   Data início string: {data_inicio_str}")
    click.echo(f"   Data fim string: {data_fim_str}")
    click.echo(f"   Date start range: {date_start_range}")
    click.echo(f"   Date end range: {date_end_range}")
    click.echo(f"   Tipo date_start_range: {type(date_start_range)}")
    click.echo(f"   Tipo date_end_range: {type(date_end_range)}")
    date_start_range_dt = datetime.combine(date_start_range, time.min, tzinfo=timezone.utc)
    date_end_range_dt = datetime.combine(date_end_range, time.max, tzinfo=timezone.utc)
    click.echo(f"\n🕐 CONVERSÃO PARA DATETIME UTC:")
    click.echo(f"   Date start range DT: {date_start_range_dt}")
    click.echo(f"   Date end range DT: {date_end_range_dt}")
    def add_date_filter(query):
        return query.filter(
            Ocorrencia.data_hora_ocorrencia >= date_start_range_dt,
            Ocorrencia.data_hora_ocorrencia <= date_end_range_dt
        )
    base_kpi_query = db.session.query(Ocorrencia)
    base_kpi_query = ocorrencia_service.apply_ocorrencia_filters(
        base_kpi_query, filters
    )
    base_kpi_query = add_date_filter(base_kpi_query)
    total_ocorrencias = base_kpi_query.count()
    click.echo(f"\n📊 RESULTADO DO DASHBOARD:")
    click.echo(f"   Total de ocorrências encontradas: {total_ocorrencias}")
    inicio_junho = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    fim_junho = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    total_direto = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_junho,
        Ocorrencia.data_hora_ocorrencia < fim_junho
    ).count()
    click.echo(f"\n🔍 COMPARAÇÃO:")
    click.echo(f"   Total direto (nosso comando): {total_direto}")
    click.echo(f"   Total dashboard: {total_ocorrencias}")
    click.echo(f"   Diferença: {total_direto - total_ocorrencias}")
    click.echo(f"\n🔍 ANÁLISE DAS DATAS:")
    click.echo(f"   Nosso início: {inicio_junho}")
    click.echo(f"   Dashboard início: {date_start_range_dt}")
    click.echo(f"   Nosso fim: {fim_junho}")
    click.echo(f"   Dashboard fim: {date_end_range_dt}")
    ocorrencias_dashboard_dates = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= date_start_range_dt,
        Ocorrencia.data_hora_ocorrencia <= date_end_range_dt
    ).count()
    click.echo(f"\n📊 TESTE COM DATAS DO DASHBOARD:")
    click.echo(f"   Ocorrências com datas do dashboard: {ocorrencias_dashboard_dates}")
    click.echo(f"\n🔍 VERIFICAÇÃO DE FILTROS ADICIONAIS:")
    base_query_sem_filtros = db.session.query(Ocorrencia)
    base_query_sem_filtros = add_date_filter(base_query_sem_filtros)
    total_sem_filtros = base_query_sem_filtros.count()
    click.echo(f"   Total sem filtros de ocorrência: {total_sem_filtros}")
    click.echo(f"\n✅ RESUMO:")
    click.echo(f"   • Total real no banco (junho/2025): {total_direto}")
    click.echo(f"   • Total do dashboard: {total_ocorrencias}")
    click.echo(f"   • Total com datas do dashboard: {ocorrencias_dashboard_dates}")
    click.echo(f"   • Total sem filtros adicionais: {total_sem_filtros}")
    if total_ocorrencias != 188:
        click.echo(f"\n❌ PROBLEMA IDENTIFICADO:")
        click.echo(f"   O dashboard está mostrando {total_ocorrencias} em vez de 188")
        click.echo(f"   Diferença: {188 - total_ocorrencias} ocorrências")
    logger.info(f"Teste dos filtros do dashboard concluído. Dashboard: {total_ocorrencias}, Real: {total_direto}")

# 9. contar_ocorrencias_30_06_2025_command
@click.command("contar-ocorrencias-30-06-2025")
@with_appcontext
def contar_ocorrencias_30_06_2025_command():
    """
    Conta e mostra a quantidade de ocorrências registradas no dia 30/06/2025.
    Exibe estatísticas resumidas por status e tipo.
    """
    from datetime import datetime, timezone
    from app.models import Ocorrencia, OcorrenciaTipo
    logger = logging.getLogger(__name__)
    click.echo("=== CONTAGEM DE OCORRÊNCIAS - 30/06/2025 ===")
    inicio_dia = datetime(2025, 6, 30, 0, 0, 0, tzinfo=timezone.utc)
    fim_dia = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    total_ocorrencias = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_dia,
        Ocorrencia.data_hora_ocorrencia < fim_dia
    ).count()
    click.echo(f"\n📊 RESULTADO:")
    click.echo(f"   Total de ocorrências em 30/06/2025: {total_ocorrencias}")
    if total_ocorrencias == 0:
        click.echo("❌ Nenhuma ocorrência encontrada para 30/06/2025.")
        return
    from sqlalchemy import func
    status_stats = (
        db.session.query(
            Ocorrencia.status,
            func.count(Ocorrencia.id).label('quantidade')
        )
        .filter(
            Ocorrencia.data_hora_ocorrencia >= inicio_dia,
            Ocorrencia.data_hora_ocorrencia < fim_dia
        )
        .group_by(Ocorrencia.status)
        .order_by(func.count(Ocorrencia.id).desc())
        .all()
    )
    click.echo(f"\n📈 ESTATÍSTICAS POR STATUS:")
    for status, quantidade in status_stats:
        percentual = (quantidade / total_ocorrencias) * 100
        click.echo(f"   • {status}: {quantidade} ({percentual:.1f}%)")
    tipo_stats = (
        db.session.query(
            OcorrenciaTipo.nome,
            func.count(Ocorrencia.id).label('quantidade')
        )
        .join(Ocorrencia, Ocorrencia.ocorrencia_tipo_id == OcorrenciaTipo.id)
        .filter(
            Ocorrencia.data_hora_ocorrencia >= inicio_dia,
            Ocorrencia.data_hora_ocorrencia < fim_dia
        )
        .group_by(OcorrenciaTipo.nome)
        .order_by(func.count(Ocorrencia.id).desc())
        .all()
    )
    click.echo(f"\n📋 ESTATÍSTICAS POR TIPO:")
    for tipo, quantidade in tipo_stats:
        percentual = (quantidade / total_ocorrencias) * 100
        click.echo(f"   • {tipo}: {quantidade} ({percentual:.1f}%)")
    hora_stats = (
        db.session.query(
            func.extract('hour', Ocorrencia.data_hora_ocorrencia).label('hora'),
            func.count(Ocorrencia.id).label('quantidade')
        )
        .filter(
            Ocorrencia.data_hora_ocorrencia >= inicio_dia,
            Ocorrencia.data_hora_ocorrencia < fim_dia
        )
        .group_by(func.extract('hour', Ocorrencia.data_hora_ocorrencia))
        .order_by(func.extract('hour', Ocorrencia.data_hora_ocorrencia))
        .all()
    )
    click.echo(f"\n🕐 ESTATÍSTICAS POR HORA:")
    for hora, quantidade in hora_stats:
        percentual = (quantidade / total_ocorrencias) * 100
        click.echo(f"   • {int(hora):02d}:00 - {int(hora):02d}:59: {quantidade} ({percentual:.1f}%)")
    click.echo(f"\n✅ RESUMO:")
    click.echo(f"   • Data: 30/06/2025")
    click.echo(f"   • Total de ocorrências: {total_ocorrencias}")
    if status_stats:
        status_mais_comum = status_stats[0]
        click.echo(f"   • Status mais comum: {status_mais_comum[0]} ({status_mais_comum[1]})")
    if tipo_stats:
        tipo_mais_comum = tipo_stats[0]
        click.echo(f"   • Tipo mais comum: {tipo_mais_comum[0]} ({tipo_mais_comum[1]})")
    if hora_stats:
        hora_mais_ativa = max(hora_stats, key=lambda x: x[1])
        click.echo(f"   • Hora mais ativa: {int(hora_mais_ativa[0]):02d}:00 ({hora_mais_ativa[1]} ocorrências)")
    logger.info(f"Contagem de ocorrências de 30/06/2025 concluída. Total: {total_ocorrencias}")

# 10. test_ronda_duplicada_command
@click.command("test-ronda-duplicada")
@click.argument("condominio_nome")
@click.argument("data_plantao")
@click.argument("turno_ronda")
@with_appcontext
def test_ronda_duplicada_command(condominio_nome, data_plantao, turno_ronda):
    """
    Testa se existe uma ronda para o condomínio, data e turno informados.
    Exemplo de uso:
    flask test-ronda-duplicada "AROSA" 2025-07-14 "Noturno Par"
    """
    from app.models import Condominio, Ronda
    from datetime import datetime
    import click
    cond = Condominio.query.filter_by(nome=condominio_nome).first()
    if not cond:
        click.echo(f"Condomínio '{condominio_nome}' não encontrado.")
        return
    try:
        data_dt = datetime.strptime(data_plantao, "%Y-%m-%d").date()
    except Exception as e:
        click.echo(f"Data inválida: {e}")
        return
    rondas = Ronda.query.filter_by(
        condominio_id=cond.id,
        data_plantao_ronda=data_dt,
        turno_ronda=turno_ronda
    ).all()
    if not rondas:
        click.echo("Nenhuma ronda encontrada para esses parâmetros.")
    else:
        click.echo(f"{len(rondas)} ronda(s) encontrada(s):")
        for r in rondas:
            click.echo(f"ID: {r.id} | Data: {r.data_plantao_ronda} | Turno: {r.turno_ronda} | Condominio: {cond.nome} | user_id: {r.user_id}")

# 11. listar_rondas_condominio_data_command
@click.command("listar-rondas-condominio-data")
@click.argument("condominio_nome")
@click.argument("data_plantao")
@with_appcontext
def listar_rondas_condominio_data_command(condominio_nome, data_plantao):
    """
    Lista todas as rondas para o condomínio e data informados, mostrando todos os turnos.
    Exemplo de uso:
    flask listar-rondas-condominio-data "AROSA" 2025-07-14
    """
    from app.models import Condominio, Ronda
    from datetime import datetime
    import click
    cond = Condominio.query.filter_by(nome=condominio_nome).first()
    if not cond:
        click.echo(f"Condomínio '{condominio_nome}' não encontrado.")
        return
    try:
        data_dt = datetime.strptime(data_plantao, "%Y-%m-%d").date()
    except Exception as e:
        click.echo(f"Data inválida: {e}")
        return
    rondas = Ronda.query.filter_by(
        condominio_id=cond.id,
        data_plantao_ronda=data_dt
    ).all()
    if not rondas:
        click.echo("Nenhuma ronda encontrada para esses parâmetros.")
    else:
        click.echo(f"{len(rondas)} ronda(s) encontrada(s):")
        for r in rondas:
            click.echo(f"ID: {r.id} | Data: {r.data_plantao_ronda} | Turno: '{r.turno_ronda}' | Condominio: {cond.nome} | user_id: {r.user_id} | Escala: '{r.escala_plantao}'")

@click.command("logins-hoje")
@with_appcontext
def logins_hoje_command():
    """
    Lista todos os usuários que fizeram login com sucesso hoje.
    """
    from datetime import datetime, timezone
    from app.models import LoginHistory, User
    today = datetime.now(timezone.utc).date()
    logins_hoje = (
        db.session.query(User.id, User.username, LoginHistory.timestamp)
        .join(LoginHistory, LoginHistory.user_id == User.id)
        .filter(
            LoginHistory.success == True,
            db.func.date(LoginHistory.timestamp) == today
        )
        .order_by(LoginHistory.timestamp.desc())
        .all()
    )
    click.echo("--- USUÁRIOS QUE FIZERAM LOGIN HOJE ---")
    if not logins_hoje:
        click.echo("Nenhum login registrado hoje.")
        return
    for user_id, username, timestamp in logins_hoje:
        click.echo(f"ID: {user_id} | Usuário: {username} | Login: {timestamp}") 