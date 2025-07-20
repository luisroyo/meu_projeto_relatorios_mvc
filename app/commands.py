# app/commands.py

import logging
import os
from datetime import timedelta

import click
from flask.cli import with_appcontext

from app.models import EscalaMensal, Ocorrencia, Ronda, User, Condominio

from . import db

logger = logging.getLogger(__name__)


@click.command("seed-db")
@with_appcontext
def seed_db_command():
    """
    Cria usuários administradores e supervisores padrão para desenvolvimento.
    AVISO: Nunca use este comando em produção! As senhas são fracas e conhecidas.
    Para produção, crie usuários manualmente ou implemente um fluxo seguro.
    """
    # Para produção, use variáveis de ambiente ou um prompt seguro
    default_users = [
        # Campos extras (password) não são passados ao construtor User diretamente
        {
            "username": "Luis Royo",
            "email": "luisroyo25@gmail.com",
            "is_admin": True,
            "is_supervisor": True,
            "is_approved": True,
            "password": os.getenv("ADMIN_PASSWORD", "dev123"),
        },
        {
            "username": "Romel / Arnaldo",
            "email": "romel.arnaldo@example.com",
            "is_admin": False,
            "is_supervisor": True,
            "is_approved": True,
            "password": os.getenv("SUPERVISOR_PASSWORD", "dev123"),
        },
        {
            "username": "Gleison",
            "email": "gleison@example.com",
            "is_admin": False,
            "is_supervisor": True,
            "is_approved": True,
            "password": os.getenv("SUPERVISOR2_PASSWORD", "dev123"),
        },
        {
            "username": "Douglas",
            "email": "douglas@example.com",
            "is_admin": False,
            "is_supervisor": True,
            "is_approved": True,
            "password": os.getenv("SUPERVISOR3_PASSWORD", "dev123"),
        },
    ]
    for user_data in default_users:
        try:
            user_exists = User.query.filter_by(email=user_data["email"]).first()
            if not user_exists:
                # Só passa os campos válidos para o construtor User
                new_user = User(
                    username=user_data["username"],  # type: ignore
                    email=user_data["email"],  # type: ignore
                    is_admin=user_data.get("is_admin", False),  # type: ignore
                    is_supervisor=user_data.get("is_supervisor", False),  # type: ignore
                    is_approved=user_data.get("is_approved", True),  # type: ignore
                )
                new_user.set_password(user_data["password"])
                db.session.add(new_user)
                logger.info(f"Usuário '{user_data['username']}' criado com sucesso.")
                click.echo(f"Usuário '{user_data['username']}' criado com sucesso.")
            else:
                if user_data.get("is_supervisor") and not user_exists.is_supervisor:
                    user_exists.is_supervisor = True
                    logger.info(
                        f"Usuário '{user_data['username']}' atualizado para supervisor."
                    )
                    click.echo(
                        f"Usuário '{user_data['username']}' atualizado para supervisor."
                    )
                else:
                    click.echo(f"Usuário '{user_data['username']}' já existe.")
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Falha ao criar/atualizar usuário '{user_data['username']}': {e}",
                exc_info=True,
            )
            click.echo(f"Erro ao processar usuário '{user_data['username']}': {e}")
            return
    db.session.commit()
    logger.info("Comando de inicialização do banco de dados concluído.")
    click.echo("Comando de inicialização do banco de dados concluído.")


@click.command("assign-supervisors")
@with_appcontext
def assign_supervisors_command():
    """
    Sincroniza TODAS as rondas existentes com as escalas mensais definidas na interface.
    Atualiza supervisor_id nas rondas conforme a escala vigente.
    """
    click.echo(
        "Iniciando sincronização em massa de supervisores para TODAS as rondas..."
    )
    try:
        periodos_com_rondas = (
            db.session.query(
                db.extract("year", Ronda.data_plantao_ronda).label("ano"),
                db.extract("month", Ronda.data_plantao_ronda).label("mes"),
            )
            .distinct()
            .all()
        )

        if not periodos_com_rondas:
            click.echo("Nenhuma ronda encontrada no banco de dados para sincronizar.")
            return

        click.echo(
            f"Encontrados {len(periodos_com_rondas)} períodos distintos (mês/ano) com rondas."
        )
        total_geral_updated = 0
        for periodo in periodos_com_rondas:
            ano, mes = periodo.ano, periodo.mes
            escalas_do_mes = EscalaMensal.query.filter_by(ano=ano, mes=mes).all()
            if not escalas_do_mes:
                click.echo(
                    f"-> Pulando período {mes}/{ano}: Nenhuma escala definida na interface."
                )
                continue

            mapa_escala = {
                escala.nome_turno: escala.supervisor_id for escala in escalas_do_mes
            }
            click.echo(
                f"-> Processando período {mes}/{ano} com a escala: {mapa_escala}"
            )
            periodo_updated_count = 0
            for turno, supervisor_id in mapa_escala.items():
                updated_rows = (
                    db.session.query(Ronda)
                    .filter(
                        db.extract("year", Ronda.data_plantao_ronda) == ano,
                        db.extract("month", Ronda.data_plantao_ronda) == mes,
                    Ronda.turno_ronda == turno,
                        Ronda.supervisor_id != supervisor_id,
                    )
                    .update({"supervisor_id": supervisor_id}, synchronize_session=False)
                )
                
                if updated_rows > 0:
                    periodo_updated_count += updated_rows

            if periodo_updated_count > 0:
                click.echo(
                    f"   - {periodo_updated_count} rondas atualizadas para {mes}/{ano}."
                )
                total_geral_updated += periodo_updated_count

        db.session.commit()
        logger.info(
            f"Operação concluída! Total de {total_geral_updated} rondas atualizadas em todos os períodos."
        )
        click.echo(
            f"\nOperação concluída! Total de {total_geral_updated} rondas atualizadas em todos os períodos."
        )
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Falha na atribuição em massa de supervisores: {e}", exc_info=True
        )
        click.echo(f"ERRO: A operação falhou e foi revertida. Detalhes: {e}")


@click.command("fix-ocorrencias-definitive")
@with_appcontext
def fix_ocorrencias_definitive_command():
    """
    CORREÇÃO FINAL: Subtrai 6 horas dos registros de Ocorrências que foram
    ajustados incorretamente, deixando-os no formato UTC correto.
    Este comando NÃO AFETA a tabela de Rondas.
    Use apenas se você sabe o que está fazendo!
    """
    logger.warning(
        "INICIANDO SCRIPT DE CORREÇÃO FINAL PARA OCORRÊNCIAS - USE COM CAUTELA!"
    )
    click.echo("--- INICIANDO SCRIPT DE CORREÇÃO FINAL PARA OCORRÊNCIAS ---")

    updated_ocorrencias = 0

    for ocorrencia in Ocorrencia.query.all():
        if (
            ocorrencia.data_hora_ocorrencia
            and ocorrencia.data_hora_ocorrencia.tzinfo is not None
        ):
            ocorrencia.data_hora_ocorrencia = (
                ocorrencia.data_hora_ocorrencia - timedelta(hours=6)
            )
            updated_ocorrencias += 1

    if updated_ocorrencias > 0:
        try:
            db.session.commit()
            logger.info(
                f"SUCESSO: {updated_ocorrencias} registros de ocorrências foram corrigidos."
            )
            click.echo(
                f"\nSUCESSO: {updated_ocorrencias} registros de ocorrências foram corrigidos."
            )
            click.echo(
                "Por favor, verifique os dados no sistema. O problema de fuso horário deve estar resolvido."
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Falha ao salvar as correções: {e}", exc_info=True)
            click.echo(
                f"\nERRO: Falha ao salvar as correções. Nenhuma mudança foi feita. Erro: {e}"
            )
    else:
        click.echo(
            "\nNenhuma ocorrência com fuso horário ('aware') foi encontrada para corrigir."
        )
        logger.info(
            "Nenhuma ocorrência com fuso horário ('aware') foi encontrada para corrigir."
        )


@click.command("check-ocorrencias-data")
@with_appcontext
def check_ocorrencias_data_command():
    """
    Verifica os dados de ocorrências no banco de dados para debug do dashboard.
    """
    from app.models import Ocorrencia
    
    logger.info("Verificando dados de ocorrências no banco de dados...")
    click.echo("--- VERIFICAÇÃO DE DADOS DE OCORRÊNCIAS ---")
    
    # Conta total de ocorrências
    total_ocorrencias = Ocorrencia.query.count()
    click.echo(f"Total de ocorrências no banco: {total_ocorrencias}")
    
    if total_ocorrencias == 0:
        click.echo("❌ NENHUMA OCORRÊNCIA ENCONTRADA NO BANCO DE DADOS!")
        click.echo("Este é o motivo pelo qual o gráfico de evolução diária não aparece.")
        return
    
    # Mostra algumas ocorrências de exemplo
    ocorrencias_exemplo = Ocorrencia.query.order_by(Ocorrencia.data_hora_ocorrencia.desc()).limit(5).all()
    click.echo(f"\nÚltimas 5 ocorrências:")
    for oc in ocorrencias_exemplo:
        click.echo(f"  ID: {oc.id}, Data: {oc.data_hora_ocorrencia}, Status: {oc.status}")
    
    # Verifica ocorrências por mês atual
    from datetime import datetime, timezone
    hoje = datetime.now(timezone.utc)
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    ocorrencias_mes_atual = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= primeiro_dia_mes
    ).count()
    
    click.echo(f"\nOcorrências no mês atual ({hoje.strftime('%B/%Y')}): {ocorrencias_mes_atual}")
    
    # Verifica ocorrências por dia nos últimos 7 dias
    from datetime import timedelta
    sete_dias_atras = hoje - timedelta(days=7)
    
    ocorrencias_ultimos_7_dias = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= sete_dias_atras
    ).order_by(Ocorrencia.data_hora_ocorrencia.desc()).all()
    
    click.echo(f"\nOcorrências nos últimos 7 dias: {len(ocorrencias_ultimos_7_dias)}")
    for oc in ocorrencias_ultimos_7_dias:
        click.echo(f"  {oc.data_hora_ocorrencia.strftime('%d/%m/%Y %H:%M')} - {oc.status}")


@click.command("check-rondas-monthly")
@with_appcontext
def check_rondas_monthly_command():
    """
    Verifica os dados reais de rondas por mês para debug do dashboard comparativo.
    """
    from app.models import Ronda
    from sqlalchemy import func
    from datetime import datetime
    
    logger.info("Verificando dados reais de rondas por mês...")
    click.echo("--- VERIFICAÇÃO DE DADOS REAIS DE RONDAS POR MÊS ---")
    
    # Verifica o ano atual
    current_year = datetime.now().year
    click.echo(f"Ano atual: {current_year}")
    
    # Busca dados reais por mês usando a mesma query do dashboard
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
    
    # Verifica total geral
    total_geral = sum(total for _, total in query_result)
    click.echo(f"\nTotal geral: {total_geral} rondas")
    
    # Verifica se há dados sem data_plantao_ronda
    rondas_sem_data = Ronda.query.filter(Ronda.data_plantao_ronda.is_(None)).count()
    if rondas_sem_data > 0:
        click.echo(f"⚠️  ATENÇÃO: {rondas_sem_data} rondas sem data_plantao_ronda!")
    
    # Verifica dados por data_hora_inicio (alternativa)
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


@click.command("test-media-dia-trabalhado")
@with_appcontext
def test_media_dia_trabalhado_command():
    """
    Testa a nova métrica de média por dia trabalhado considerando escala 12x36.
    """
    from app.services.dashboard.comparativo_dashboard import _calculate_working_days_in_period
    from datetime import datetime, date
    
    logger.info("Testando métrica de média por dia trabalhado...")
    click.echo("--- TESTE DA MÉTRICA DE MÉDIA POR DIA TRABALHADO ---")
    
    # Testa para o ano atual
    current_year = datetime.now().year
    start_date = date(current_year, 1, 1)
    end_date = date(current_year, 12, 31)
    
    working_days = _calculate_working_days_in_period(start_date, end_date)
    total_days = (end_date - start_date).days + 1
    
    click.echo(f"Ano: {current_year}")
    click.echo(f"Total de dias no ano: {total_days}")
    click.echo(f"Dias trabalhados (escala 12x36): {working_days}")
    click.echo(f"Proporção: {working_days}/{total_days} = {round(working_days/total_days*100, 1)}%")
    
    # Testa com dados reais
    from app.models import Ronda
    from sqlalchemy import func
    
    total_rondas = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).scalar()
    
    media_rondas_dia_trabalhado = round(total_rondas / working_days, 1) if working_days > 0 else 0
    media_rondas_mes = round(total_rondas / 12, 1) if total_rondas > 0 else 0
    
    click.echo(f"\nDados reais:")
    click.echo(f"Total de rondas: {total_rondas}")
    click.echo(f"Média por mês (tradicional): {media_rondas_mes}")
    click.echo(f"Média por dia trabalhado (12x36): {media_rondas_dia_trabalhado}")
    
    # Testa para diferentes períodos
    click.echo(f"\nTestes para diferentes períodos:")
    
    # Janeiro 2025
    jan_start = date(2025, 1, 1)
    jan_end = date(2025, 1, 31)
    jan_working = _calculate_working_days_in_period(jan_start, jan_end)
    click.echo(f"Janeiro 2025: {jan_working} dias trabalhados de 31 dias")
    
    # Fevereiro 2025
    fev_start = date(2025, 2, 1)
    fev_end = date(2025, 2, 28)
    fev_working = _calculate_working_days_in_period(fev_start, fev_end)
    click.echo(f"Fevereiro 2025: {fev_working} dias trabalhados de 28 dias")
    
    # Junho 2025 (mês com dados)
    jun_start = date(2025, 6, 1)
    jun_end = date(2025, 6, 30)
    jun_working = _calculate_working_days_in_period(jun_start, jun_end)
    click.echo(f"Junho 2025: {jun_working} dias trabalhados de 30 dias")
    
    # Calcula média de junho
    rondas_junho = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == "2025-06"
    ).scalar()
    
    media_junho_dia_trabalhado = round(rondas_junho / jun_working, 1) if jun_working > 0 else 0
    click.echo(f"Rondas em junho: {rondas_junho}")
    click.echo(f"Média de junho por dia trabalhado: {media_junho_dia_trabalhado}")


@click.command("investigate-rondas-discrepancy")
@with_appcontext
def investigate_rondas_discrepancy_command():
    """
    Investiga a discrepância nos dados de rondas entre diferentes queries.
    """
    from app.models import Ronda
    from sqlalchemy import func
    from datetime import datetime
    
    logger.info("Investigando discrepância nos dados de rondas...")
    click.echo("--- INVESTIGAÇÃO DE DISCREPÂNCIA NOS DADOS DE RONDAS ---")
    
    # Query 1: Total geral sem filtro de ano
    total_geral = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).scalar()
    click.echo(f"1. Total geral (sem filtro de ano): {total_geral}")
    
    # Query 2: Total por ano atual
    current_year = datetime.now().year
    total_ano_atual = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year)
    ).scalar()
    click.echo(f"2. Total ano {current_year}: {total_ano_atual}")
    
    # Query 3: Contagem de registros por ano
    registros_por_ano = db.session.query(
        func.to_char(Ronda.data_plantao_ronda, "YYYY").label("ano"),
        func.count(Ronda.id).label("registros"),
        func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("rondas")
    ).group_by(func.to_char(Ronda.data_plantao_ronda, "YYYY")).order_by("ano").all()
    
    click.echo(f"\n3. Dados por ano:")
    for ano, registros, rondas in registros_por_ano:
        click.echo(f"   {ano}: {registros} registros, {rondas} rondas")
    
    # Query 4: Verificar registros sem data_plantao_ronda
    registros_sem_data = Ronda.query.filter(Ronda.data_plantao_ronda.is_(None)).count()
    click.echo(f"\n4. Registros sem data_plantao_ronda: {registros_sem_data}")
    
    if registros_sem_data > 0:
        rondas_sem_data = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
            Ronda.data_plantao_ronda.is_(None)
        ).scalar()
        click.echo(f"   Rondas em registros sem data: {rondas_sem_data}")
    
    # Query 5: Verificar registros com total_rondas_no_log NULL
    registros_null_rondas = Ronda.query.filter(Ronda.total_rondas_no_log.is_(None)).count()
    click.echo(f"\n5. Registros com total_rondas_no_log NULL: {registros_null_rondas}")
    
    # Query 6: Verificar registros com total_rondas_no_log = 0
    registros_zero_rondas = Ronda.query.filter(Ronda.total_rondas_no_log == 0).count()
    click.echo(f"6. Registros com total_rondas_no_log = 0: {registros_zero_rondas}")
    
    # Query 7: Amostra de registros
    click.echo(f"\n7. Amostra de registros (primeiros 5):")
    amostra = Ronda.query.limit(5).all()
    for ronda in amostra:
        click.echo(f"   ID: {ronda.id}, Data: {ronda.data_plantao_ronda}, Rondas: {ronda.total_rondas_no_log}")


@click.command("test-media-dias-reais")
@with_appcontext
def test_media_dias_reais_command():
    """
    Testa o cálculo de média baseado nos dias reais trabalhados pelos supervisores.
    """
    from app.models import Ronda, User
    from sqlalchemy import func
    from datetime import datetime
    
    logger.info("Testando média baseada em dias reais trabalhados...")
    click.echo("--- TESTE DE MÉDIA BASEADA EM DIAS REAIS TRABALHADOS ---")
    
    current_year = datetime.now().year
    
    # 1. Total de rondas no ano
    total_rondas = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year)
    ).scalar()
    
    click.echo(f"Total de rondas em {current_year}: {total_rondas}")
    
    # 2. Dias únicos trabalhados (por data_plantao_ronda)
    dias_trabalhados = db.session.query(
        func.count(func.distinct(Ronda.data_plantao_ronda))
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year)
    ).scalar()
    
    click.echo(f"Dias únicos trabalhados: {dias_trabalhados}")
    
    # 3. Média por dia real trabalhado
    media_dia_real = round(total_rondas / dias_trabalhados, 1) if dias_trabalhados > 0 else 0
    click.echo(f"Média por dia real trabalhado: {media_dia_real}")
    
    # 4. Comparação com cálculo teórico (12x36)
    from app.services.dashboard.comparativo_dashboard import _calculate_working_days_in_period
    from datetime import date
    
    start_date = date(current_year, 1, 1)
    end_date = date(current_year, 12, 31)
    dias_teoricos = _calculate_working_days_in_period(start_date, end_date)
    media_teorica = round(total_rondas / dias_teoricos, 1) if dias_teoricos > 0 else 0
    
    click.echo(f"\nComparação:")
    click.echo(f"Dias teóricos (12x36): {dias_teoricos}")
    click.echo(f"Dias reais trabalhados: {dias_trabalhados}")
    click.echo(f"Média teórica: {media_teorica}")
    click.echo(f"Média real: {media_dia_real}")
    
    # 5. Análise por supervisor
    click.echo(f"\nAnálise por supervisor:")
    supervisores_dados = db.session.query(
        User.username,
        func.count(func.distinct(Ronda.data_plantao_ronda)).label("dias_trabalhados"),
        func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total_rondas")
    ).join(Ronda, User.id == Ronda.supervisor_id).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year)
    ).group_by(User.username).order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc()).all()
    
    for supervisor, dias, rondas in supervisores_dados:
        media_supervisor = round(rondas / dias, 1) if dias > 0 else 0
        click.echo(f"  {supervisor}: {dias} dias, {rondas} rondas, {media_supervisor}/dia")
    
    # 6. Análise por mês
    click.echo(f"\nAnálise por mês:")
    meses_dados = db.session.query(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM").label("mes"),
        func.count(func.distinct(Ronda.data_plantao_ronda)).label("dias_trabalhados"),
        func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total_rondas")
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year)
    ).group_by(func.to_char(Ronda.data_plantao_ronda, "YYYY-MM")).order_by("mes").all()
    
    for mes, dias, rondas in meses_dados:
        media_mes = round(rondas / dias, 1) if dias > 0 else 0
        click.echo(f"  {mes}: {dias} dias, {rondas} rondas, {media_mes}/dia")
    
    # 7. Verificar se há dias sem supervisor
    dias_sem_supervisor = db.session.query(
        func.count(func.distinct(Ronda.data_plantao_ronda))
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year),
        Ronda.supervisor_id.is_(None)
    ).scalar()
    
    if dias_sem_supervisor > 0:
        click.echo(f"\n⚠️  Dias sem supervisor: {dias_sem_supervisor}")


@click.command("check-supervisor-working-days")
@with_appcontext
def check_supervisor_working_days_command():
    """
    Verifica exatamente quantos dias cada supervisor trabalhou em um mês específico.
    """
    from app.models import Ronda, User
    from sqlalchemy import func
    from datetime import datetime
    
    logger.info("Verificando dias trabalhados por supervisor...")
    click.echo("--- VERIFICAÇÃO DE DIAS TRABALHADOS POR SUPERVISOR ---")
    
    # Parâmetros
    year = 2025
    month = 6  # Junho
    
    click.echo(f"Análise para {year}-{month:02d}")
    
    # 1. Total de rondas no mês
    total_rondas_mes = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == f"{year}-{month:02d}"
    ).scalar()
    
    click.echo(f"Total de rondas em {year}-{month:02d}: {total_rondas_mes}")
    
    # 2. Dias únicos no mês (método atual)
    dias_unicos_mes = db.session.query(
        func.count(func.distinct(Ronda.data_plantao_ronda))
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == f"{year}-{month:02d}"
    ).scalar()
    
    click.echo(f"Dias únicos no mês: {dias_unicos_mes}")
    
    # 3. Média atual
    media_atual = round(total_rondas_mes / dias_unicos_mes, 1) if dias_unicos_mes > 0 else 0
    click.echo(f"Média atual: {media_atual}")
    
    # 4. Análise detalhada por supervisor
    click.echo(f"\nAnálise detalhada por supervisor:")
    supervisores_detalhado = db.session.query(
        User.username,
        func.count(func.distinct(Ronda.data_plantao_ronda)).label("dias_trabalhados"),
        func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("total_rondas"),
        func.array_agg(func.distinct(Ronda.data_plantao_ronda)).label("datas_trabalhadas")
    ).join(Ronda, User.id == Ronda.supervisor_id).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == f"{year}-{month:02d}"
    ).group_by(User.username).order_by(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).desc()).all()
    
    for supervisor, dias, rondas, datas in supervisores_detalhado:
        media_supervisor = round(rondas / dias, 1) if dias > 0 else 0
        click.echo(f"\n  {supervisor}:")
        click.echo(f"    Dias trabalhados: {dias}")
        click.echo(f"    Total de rondas: {rondas}")
        click.echo(f"    Média: {media_supervisor}/dia")
        click.echo(f"    Datas: {sorted(datas)}")
    
    # 5. Verificar se há registros sem supervisor
    registros_sem_supervisor = db.session.query(
        func.count(func.distinct(Ronda.data_plantao_ronda))
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == f"{year}-{month:02d}",
        Ronda.supervisor_id.is_(None)
    ).scalar()
    
    if registros_sem_supervisor > 0:
        click.echo(f"\n⚠️  Dias sem supervisor: {registros_sem_supervisor}")
        
        # Mostrar datas sem supervisor
        datas_sem_supervisor = db.session.query(
            func.distinct(Ronda.data_plantao_ronda)
        ).filter(
            func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == f"{year}-{month:02d}",
            Ronda.supervisor_id.is_(None)
        ).all()
        
        click.echo(f"    Datas: {[d[0] for d in datas_sem_supervisor]}")
    
    # 6. Verificar se há múltiplos registros no mesmo dia
    click.echo(f"\nVerificando múltiplos registros por dia:")
    dias_com_multiplos = db.session.query(
        Ronda.data_plantao_ronda,
        func.count(Ronda.id).label("registros"),
        func.coalesce(func.sum(Ronda.total_rondas_no_log), 0).label("rondas")
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == f"{year}-{month:02d}"
    ).group_by(Ronda.data_plantao_ronda).having(func.count(Ronda.id) > 1).order_by(Ronda.data_plantao_ronda).all()
    
    for data, registros, rondas in dias_com_multiplos:
        click.echo(f"  {data}: {registros} registros, {rondas} rondas")


@click.command("test-supervisor-specific")
@with_appcontext
def test_supervisor_specific_command():
    """
    Testa a correção da média por supervisor específico.
    """
    from app.services.dashboard.comparativo_dashboard import _calculate_supervisor_specific_metrics
    from app.models import User
    from datetime import datetime
    
    logger.info("Testando média específica por supervisor...")
    click.echo("--- TESTE DE MÉDIA ESPECÍFICA POR SUPERVISOR ---")
    
    current_year = datetime.now().year
    
    # Busca o supervisor Luis Royo
    luis_royo = User.query.filter_by(username="Luis Royo").first()
    if not luis_royo:
        click.echo("❌ Supervisor 'Luis Royo' não encontrado!")
        return
    
    click.echo(f"Testando para: {luis_royo.username} (ID: {luis_royo.id})")
    
    # Simula filtro de supervisor
    filters = {"supervisor_id": luis_royo.id}
    
    # Total de rondas do Luis Royo em 2025
    from app.models import Ronda
    from sqlalchemy import func
    
    total_rondas_luis = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year),
        Ronda.supervisor_id == luis_royo.id
    ).scalar()
    
    click.echo(f"Total de rondas do Luis Royo em {current_year}: {total_rondas_luis}")
    
    # Testa a função corrigida
    media_corrigida, dias_corrigidos = _calculate_supervisor_specific_metrics(
        total_rondas_luis, filters, current_year
    )
    
    click.echo(f"Dias trabalhados pelo Luis Royo: {dias_corrigidos}")
    click.echo(f"Média corrigida: {media_corrigida}/dia")
    
    # Compara com o cálculo anterior (errado)
    dias_errado = db.session.query(
        func.count(func.distinct(Ronda.data_plantao_ronda))
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY") == str(current_year)
    ).scalar()
    
    media_errada = round(total_rondas_luis / dias_errado, 1) if dias_errado > 0 else 0
    
    click.echo(f"\nComparação:")
    click.echo(f"Método anterior (errado): {media_errada}/dia ({dias_errado} dias)")
    click.echo(f"Método corrigido: {media_corrigida}/dia ({dias_corrigidos} dias)")
    
    # Testa para junho especificamente
    click.echo(f"\nTeste específico para junho:")
    
    total_rondas_junho = db.session.query(func.coalesce(func.sum(Ronda.total_rondas_no_log), 0)).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == "2025-06",
        Ronda.supervisor_id == luis_royo.id
    ).scalar()
    
    dias_junho = db.session.query(
        func.count(func.distinct(Ronda.data_plantao_ronda))
    ).filter(
        func.to_char(Ronda.data_plantao_ronda, "YYYY-MM") == "2025-06",
        Ronda.supervisor_id == luis_royo.id
    ).scalar()
    
    media_junho = round(total_rondas_junho / dias_junho, 1) if dias_junho > 0 else 0
    
    click.echo(f"Junho - Total: {total_rondas_junho}, Dias: {dias_junho}, Média: {media_junho}/dia")


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

    # 1. Lista todas as ocorrências do mês
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

    # 2. Dias distintos com ocorrências
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

    # 3. Ocorrências após o período (para checagem)
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


@click.command("contar-ocorrencias-30-06-2025")
@with_appcontext
def contar_ocorrencias_30_06_2025_command():
    """
    Conta e mostra a quantidade de ocorrências registradas no dia 30/06/2025.
    Exibe estatísticas resumidas por status e tipo.
    """
    from datetime import datetime, timezone
    from app.models import Ocorrencia, OcorrenciaTipo
    
    logger.info("Iniciando contagem de ocorrências do dia 30/06/2025...")
    click.echo("=== CONTAGEM DE OCORRÊNCIAS - 30/06/2025 ===")
    
    # Define o período do dia 30/06/2025 (00:00:00 até 23:59:59)
    inicio_dia = datetime(2025, 6, 30, 0, 0, 0, tzinfo=timezone.utc)
    fim_dia = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # Conta total de ocorrências do dia
    total_ocorrencias = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_dia,
        Ocorrencia.data_hora_ocorrencia < fim_dia
    ).count()
    
    click.echo(f"\n📊 RESULTADO:")
    click.echo(f"   Total de ocorrências em 30/06/2025: {total_ocorrencias}")
    
    if total_ocorrencias == 0:
        click.echo("❌ Nenhuma ocorrência encontrada para 30/06/2025.")
        return
    
    # Estatísticas por status
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
    
    # Estatísticas por tipo
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
    
    # Estatísticas por hora do dia
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
    
    # Resumo final
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
    
    logger.info("Iniciando investigação da discrepância de ocorrências de junho de 2025...")
    click.echo("=== INVESTIGAÇÃO DE DISCREPÂNCIA - JUNHO DE 2025 ===")
    
    # Define o período de junho de 2025
    inicio_junho = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    fim_junho = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    click.echo(f"\n📊 ANÁLISE GERAL:")
    click.echo(f"   Período analisado: 01/06/2025 a 30/06/2025")
    click.echo(f"   Início UTC: {inicio_junho}")
    click.echo(f"   Fim UTC: {fim_junho}")
    
    # 1. Total geral de ocorrências no banco
    total_geral = Ocorrencia.query.count()
    click.echo(f"\n🔍 TOTAL GERAL NO BANCO:")
    click.echo(f"   Total de ocorrências no banco: {total_geral}")
    
    # 2. Ocorrências com data_hora_ocorrencia NULL
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
    
    # 3. Ocorrências no período (filtro principal)
    ocorrencias_periodo = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_junho,
        Ocorrencia.data_hora_ocorrencia < fim_junho
    ).count()
    click.echo(f"\n📅 OCORRÊNCIAS NO PERÍODO (FILTRO PRINCIPAL):")
    click.echo(f"   Ocorrências em junho/2025: {ocorrencias_periodo}")
    
    # 4. Ocorrências antes do período
    ocorrencias_antes = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia < inicio_junho
    ).count()
    click.echo(f"\n📅 OCORRÊNCIAS ANTES DO PERÍODO:")
    click.echo(f"   Ocorrências antes de 01/06/2025: {ocorrencias_antes}")
    
    # 5. Ocorrências após o período
    ocorrencias_depois = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= fim_junho
    ).count()
    click.echo(f"\n📅 OCORRÊNCIAS APÓS O PERÍODO:")
    click.echo(f"   Ocorrências após 30/06/2025: {ocorrencias_depois}")
    
    # 6. Verificação matemática
    total_calculado = ocorrencias_periodo + ocorrencias_antes + ocorrencias_depois + ocorrencias_sem_data
    click.echo(f"\n🧮 VERIFICAÇÃO MATEMÁTICA:")
    click.echo(f"   Período + Antes + Depois + Sem Data = {ocorrencias_periodo} + {ocorrencias_antes} + {ocorrencias_depois} + {ocorrencias_sem_data} = {total_calculado}")
    click.echo(f"   Total real no banco: {total_geral}")
    click.echo(f"   Diferença: {total_geral - total_calculado}")
    
    # 7. Análise por status no período
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
    
    # 8. Verificar ocorrências com datas estranhas
    click.echo(f"\n🔍 OCORRÊNCIAS COM DATAS ESTRANHAS:")
    
    # Ocorrências com data_hora_ocorrencia muito antiga
    ocorrencias_antigas = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia < datetime(2020, 1, 1, tzinfo=timezone.utc)
    ).count()
    click.echo(f"   Ocorrências antes de 2020: {ocorrencias_antigas}")
    
    # Ocorrências com data_hora_ocorrencia no futuro
    ocorrencias_futuras = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia > datetime.now(timezone.utc)
    ).count()
    click.echo(f"   Ocorrências no futuro: {ocorrencias_futuras}")
    
    # 9. Verificar ocorrências com data_criacao vs data_hora_ocorrencia
    click.echo(f"\n🔍 COMPARAÇÃO DATA_CRIACAO vs DATA_HORA_OCORRENCIA:")
    
    # Ocorrências criadas em junho mas com data_hora_ocorrencia diferente
    ocorrencias_criadas_junho = Ocorrencia.query.filter(
        Ocorrencia.data_criacao >= inicio_junho,
        Ocorrencia.data_criacao < fim_junho
    ).count()
    click.echo(f"   Ocorrências CRIADAS em junho/2025: {ocorrencias_criadas_junho}")
    
    # Ocorrências com data_hora_ocorrencia em junho mas criadas em outro mês
    ocorrencias_ocorridas_junho = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= inicio_junho,
        Ocorrencia.data_hora_ocorrencia < fim_junho
    ).count()
    click.echo(f"   Ocorrências OCORRIDAS em junho/2025: {ocorrencias_ocorridas_junho}")
    
    # 10. Verificar se há ocorrências duplicadas ou com problemas
    click.echo(f"\n🔍 VERIFICAÇÃO DE PROBLEMAS:")
    
    # Ocorrências com mesmo ID (impossível, mas vamos verificar)
    ids_duplicados = db.session.query(Ocorrencia.id).group_by(Ocorrencia.id).having(
        func.count(Ocorrencia.id) > 1
    ).all()
    click.echo(f"   IDs duplicados: {len(ids_duplicados)}")
    
    # 11. Resumo da investigação
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


@click.command("listar-todas-ocorrencias-junho-2025")
@with_appcontext
def listar_todas_ocorrencias_junho_2025_command():
    """
    Lista todas as 188 ocorrências de junho de 2025 com detalhes completos.
    Ajuda a identificar quais podem estar sendo excluídas da métrica.
    """
    from datetime import datetime, timezone
    from app.models import Ocorrencia, OcorrenciaTipo, Condominio, User
    
    logger.info("Listando todas as ocorrências de junho de 2025...")
    click.echo("=== LISTA COMPLETA - OCORRÊNCIAS JUNHO 2025 ===")
    
    # Define o período de junho de 2025
    inicio_junho = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    fim_junho = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # Busca todas as ocorrências do período com todos os relacionamentos
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
    
    # Análise por condomínio
    condominios_count = {}
    tipos_count = {}
    status_count = {}
    users_count = {}
    
    click.echo(f"\n📝 LISTA DETALHADA:")
    click.echo("=" * 120)
    
    for i, oc in enumerate(ocorrencias, 1):
        # Formata a data no padrão brasileiro
        data_formatada = oc.data_hora_ocorrencia.strftime('%d/%m/%Y %H:%M')
        data_criacao_formatada = oc.data_criacao.strftime('%d/%m/%Y %H:%M') if oc.data_criacao else "N/A"
        
        # Informações básicas
        condominio_nome = oc.condominio.nome if oc.condominio else "Sem condomínio"
        tipo_nome = oc.tipo.nome if oc.tipo else "Sem tipo"
        registrado_por = oc.registrado_por.username if oc.registrado_por else "N/A"
        supervisor = oc.supervisor.username if oc.supervisor else "N/A"
        
        # Contadores para análise
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
        
        # Verificar se tem relacionamentos
        if oc.orgaos_acionados:
            orgaos = [org.nome for org in oc.orgaos_acionados]
            click.echo(f"    🏛️ Órgãos: {', '.join(orgaos)}")
        
        if oc.colaboradores_envolvidos:
            colaboradores = [col.nome_completo for col in oc.colaboradores_envolvidos]
            click.echo(f"    👥 Colaboradores: {', '.join(colaboradores)}")
        
        click.echo("-" * 80)
    
    # Análise estatística
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
    
    # Verificar possíveis filtros que podem estar causando a discrepância
    click.echo(f"\n🔍 POSSÍVEIS CAUSAS DA DISCREPÂNCIA:")
    
    # Verificar ocorrências sem condomínio
    ocorrencias_sem_condominio = sum(1 for oc in ocorrencias if not oc.condominio)
    if ocorrencias_sem_condominio > 0:
        click.echo(f"   ⚠️ {ocorrencias_sem_condominio} ocorrências sem condomínio")
    
    # Verificar ocorrências sem supervisor
    ocorrencias_sem_supervisor = sum(1 for oc in ocorrencias if not oc.supervisor)
    if ocorrencias_sem_supervisor > 0:
        click.echo(f"   ⚠️ {ocorrencias_sem_supervisor} ocorrências sem supervisor")
    
    # Verificar ocorrências sem turno
    ocorrencias_sem_turno = sum(1 for oc in ocorrencias if not oc.turno)
    if ocorrencias_sem_turno > 0:
        click.echo(f"   ⚠️ {ocorrencias_sem_turno} ocorrências sem turno")
    
    # Verificar ocorrências com endereço específico
    ocorrencias_com_endereco = sum(1 for oc in ocorrencias if oc.endereco_especifico)
    click.echo(f"   📍 {ocorrencias_com_endereco} ocorrências com endereço específico")
    
    # Verificar ocorrências com órgãos acionados
    ocorrencias_com_orgaos = sum(1 for oc in ocorrencias if oc.orgaos_acionados)
    click.echo(f"   🏛️ {ocorrencias_com_orgaos} ocorrências com órgãos acionados")
    
    # Verificar ocorrências com colaboradores
    ocorrencias_com_colaboradores = sum(1 for oc in ocorrencias if oc.colaboradores_envolvidos)
    click.echo(f"   👥 {ocorrencias_com_colaboradores} ocorrências com colaboradores")
    
    click.echo(f"\n✅ INVESTIGAÇÃO CONCLUÍDA!")
    click.echo(f"   Compare esta lista com a métrica que mostra 184 ocorrências")
    click.echo(f"   para identificar quais 4 estão sendo excluídas.")
    
    logger.info(f"Listagem completa de ocorrências de junho concluída. Total: {total_ocorrencias}")


@click.command("testar-filtros-dashboard-ocorrencia")
@with_appcontext
def testar_filtros_dashboard_ocorrencia_command():
    """
    Testa os mesmos filtros usados pelo dashboard de ocorrências para identificar a discrepância.
    Simula exatamente o que o dashboard faz.
    """
    from datetime import datetime, timezone
    from app.models import Ocorrencia, OcorrenciaTipo, Condominio, User
    from app.services import ocorrencia_service
    from app.utils.date_utils import parse_date_range
    from sqlalchemy import func
    
    logger.info("Testando filtros do dashboard de ocorrências...")
    click.echo("=== TESTE DOS FILTROS DO DASHBOARD DE OCORRÊNCIAS ===")
    
    # Simula os filtros que o dashboard recebe (junho de 2025)
    filters = {
        "condominio_id": None,
        "tipo_id": None,
        "status": "",
        "supervisor_id": None,
        "mes": 6,  # Junho
        "data_inicio_str": "2025-06-01",
        "data_fim_str": "2025-06-30",
    }
    
    click.echo(f"\n📊 FILTROS APLICADOS:")
    click.echo(f"   Filtros: {filters}")
    
    # 1. Processa as datas como o dashboard faz
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
    
    # 2. Converte para datetime UTC como o dashboard faz
    from datetime import time
    date_start_range_dt = datetime.combine(date_start_range, time.min, tzinfo=timezone.utc)
    date_end_range_dt = datetime.combine(date_end_range, time.max, tzinfo=timezone.utc)
    
    click.echo(f"\n🕐 CONVERSÃO PARA DATETIME UTC:")
    click.echo(f"   Date start range DT: {date_start_range_dt}")
    click.echo(f"   Date end range DT: {date_end_range_dt}")
    
    # 3. Query base como o dashboard faz
    def add_date_filter(query):
        return query.filter(
            Ocorrencia.data_hora_ocorrencia >= date_start_range_dt,
            Ocorrencia.data_hora_ocorrencia <= date_end_range_dt
        )
    
    # 4. Query base para KPIs (exatamente como o dashboard)
    base_kpi_query = db.session.query(Ocorrencia)
    base_kpi_query = ocorrencia_service.apply_ocorrencia_filters(
        base_kpi_query, filters
    )
    base_kpi_query = add_date_filter(base_kpi_query)
    
    total_ocorrencias = base_kpi_query.count()
    click.echo(f"\n📊 RESULTADO DO DASHBOARD:")
    click.echo(f"   Total de ocorrências encontradas: {total_ocorrencias}")
    
    # 5. Comparação com nossa contagem direta
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
    
    # 6. Verificar se há diferença nos filtros de data
    click.echo(f"\n🔍 ANÁLISE DAS DATAS:")
    click.echo(f"   Nosso início: {inicio_junho}")
    click.echo(f"   Dashboard início: {date_start_range_dt}")
    click.echo(f"   Nosso fim: {fim_junho}")
    click.echo(f"   Dashboard fim: {date_end_range_dt}")
    
    # 7. Testar com as datas exatas do dashboard
    ocorrencias_dashboard_dates = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= date_start_range_dt,
        Ocorrencia.data_hora_ocorrencia <= date_end_range_dt
    ).count()
    
    click.echo(f"\n📊 TESTE COM DATAS DO DASHBOARD:")
    click.echo(f"   Ocorrências com datas do dashboard: {ocorrencias_dashboard_dates}")
    
    # 8. Verificar se há filtros adicionais sendo aplicados
    click.echo(f"\n🔍 VERIFICAÇÃO DE FILTROS ADICIONAIS:")
    
    # Testar sem aplicar filtros de ocorrência
    base_query_sem_filtros = db.session.query(Ocorrencia)
    base_query_sem_filtros = add_date_filter(base_query_sem_filtros)
    total_sem_filtros = base_query_sem_filtros.count()
    
    click.echo(f"   Total sem filtros de ocorrência: {total_sem_filtros}")
    
    # 9. Resumo final
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


@click.command("testar-dashboard-comparativo")
@with_appcontext
def testar_dashboard_comparativo_command():
    """
    Testa o dashboard comparativo para verificar se há discrepância na contagem de ocorrências.
    """
    from datetime import datetime, timezone, date, timedelta
    from app.models import Ocorrencia, Ronda
    from app.services.dashboard.comparativo.processor import DataProcessor
    from app.services.dashboard.comparativo.aggregator import DataAggregator
    from app.services.dashboard.comparativo.filters import FilterApplier
    from sqlalchemy import func
    
    logger.info("Testando dashboard comparativo...")
    click.echo("=== TESTE DO DASHBOARD COMPARATIVO ===")
    
    # Teste 1: Modo todos os meses (padrão)
    click.echo(f"\n📊 TESTE 1: MODO TODOS OS MESES (2025)")
    filters = {}
    
    try:
        rondas_series, ocorrencias_series = DataProcessor.process_all_months_mode(2025, filters)
        click.echo(f"   Série de ocorrências: {ocorrencias_series}")
        click.echo(f"   Ocorrências em junho (índice 5): {ocorrencias_series[5]}")
        
        # Comparação direta
        inicio_junho = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        fim_junho = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        total_direto = Ocorrencia.query.filter(
            Ocorrencia.data_hora_ocorrencia >= inicio_junho,
            Ocorrencia.data_hora_ocorrencia < fim_junho
        ).count()
        
        click.echo(f"   Total direto junho/2025: {total_direto}")
        click.echo(f"   Diferença: {total_direto - ocorrencias_series[5]}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro no modo todos os meses: {e}")
    
    # Teste 2: Modo mês único (junho)
    click.echo(f"\n📊 TESTE 2: MODO MÊS ÚNICO (junho/2025)")
    
    try:
        rondas_series, ocorrencias_series = DataProcessor.process_single_month_mode(2025, 6, filters)
        click.echo(f"   Série de ocorrências: {ocorrencias_series}")
        click.echo(f"   Ocorrências em junho (índice 5): {ocorrencias_series[5]}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro no modo mês único: {e}")
    
    # Teste 3: Agregador direto
    click.echo(f"\n📊 TESTE 3: AGREGADOR DIRETO")
    
    try:
        ocorrencias_raw = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, 2025, filters, is_ronda=False
        )
        click.echo(f"   Dados brutos: {ocorrencias_raw}")
        
        # Encontrar junho
        junho_data = None
        for mes_str, total in ocorrencias_raw:
            if mes_str == "2025-06":
                junho_data = total
                break
        
        click.echo(f"   Ocorrências em junho (agregador): {junho_data}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro no agregador: {e}")
    
    # Teste 4: Query manual usando o mesmo filtro do agregador
    click.echo(f"\n📊 TESTE 4: QUERY MANUAL")
    
    try:
        query = db.session.query(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
            func.count(Ocorrencia.id)
        )
        
        # Aplica filtros como o agregador faz
        query = FilterApplier.apply_ocorrencia_filters(query, filters)
        query = query.filter(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == "2025")
        
        result = (
            query.group_by(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"))
            .order_by(func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"))
            .all()
        )
        
        click.echo(f"   Resultado query manual: {result}")
        
        # Encontrar junho
        junho_manual = None
        for mes_str, total in result:
            if mes_str == "2025-06":
                junho_manual = total
                break
        
        click.echo(f"   Ocorrências em junho (manual): {junho_manual}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro na query manual: {e}")
    
    # Teste 5: Verificar se há problemas com timezone
    click.echo(f"\n📊 TESTE 5: VERIFICAÇÃO DE TIMEZONE")
    
    try:
        # Query sem timezone (como o comparativo faz)
        query_sem_tz = db.session.query(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
            func.count(Ocorrencia.id)
        ).filter(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == "2025"
        ).group_by(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM")
        ).all()
        
        click.echo(f"   Query sem timezone: {query_sem_tz}")
        
        # Query com timezone explícito
        query_com_tz = db.session.query(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
            func.count(Ocorrencia.id)
        ).filter(
            Ocorrencia.data_hora_ocorrencia >= datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            Ocorrencia.data_hora_ocorrencia < datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        ).group_by(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM")
        ).all()
        
        click.echo(f"   Query com timezone: {query_com_tz}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro na verificação de timezone: {e}")
    
    # Teste 6: Verificar ocorrências específicas de junho
    click.echo(f"\n📊 TESTE 6: OCORRÊNCIAS ESPECÍFICAS DE JUNHO")
    
    try:
        # Buscar todas as ocorrências de junho
        ocorrencias_junho = Ocorrencia.query.filter(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM") == "2025-06"
        ).all()
        
        click.echo(f"   Total ocorrências junho (func.to_char): {len(ocorrencias_junho)}")
        
        # Verificar se há ocorrências com data_hora_ocorrencia nula
        ocorrencias_nulas = Ocorrencia.query.filter(
            Ocorrencia.data_hora_ocorrencia.is_(None)
        ).count()
        
        click.echo(f"   Ocorrências com data nula: {ocorrencias_nulas}")
        
        # Verificar range de datas em junho
        datas_junho = [
            oc.data_hora_ocorrencia for oc in ocorrencias_junho 
            if oc.data_hora_ocorrencia
        ]
        
        if datas_junho:
            min_data = min(datas_junho)
            max_data = max(datas_junho)
            click.echo(f"   Data mínima em junho: {min_data}")
            click.echo(f"   Data máxima em junho: {max_data}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro na verificação específica: {e}")
    
    # Resumo final
    click.echo(f"\n✅ RESUMO DO DASHBOARD COMPARATIVO:")
    click.echo(f"   • Verifique se há diferenças entre os testes acima")
    click.echo(f"   • Se houver diferenças, pode indicar problemas de timezone ou filtros")
    click.echo(f"   • O dashboard comparativo usa func.to_char sem timezone explícito")
    
    logger.info("Teste do dashboard comparativo concluído")


@click.command("investigar-discrepancia-comparativo")
@with_appcontext
def investigar_discrepancia_comparativo_command():
    """
    Investiga especificamente a discrepância entre os modos do dashboard comparativo.
    """
    from datetime import datetime, timezone, date
    from app.models import Ocorrencia
    from app.services.dashboard.comparativo.processor import DataProcessor
    from app.services.dashboard.comparativo.aggregator import DataAggregator
    from app.services.dashboard.comparativo.filters import FilterApplier
    from sqlalchemy import func
    
    logger.info("Investigando discrepância no dashboard comparativo...")
    click.echo("=== INVESTIGAÇÃO DA DISCREPÂNCIA NO DASHBOARD COMPARATIVO ===")
    
    filters = {}
    year = 2025
    month = 6
    
    click.echo(f"\n🔍 COMPARAÇÃO DOS DOIS MODOS:")
    
    # Modo 1: Todos os meses
    click.echo(f"\n📊 MODO 1: TODOS OS MESES")
    try:
        rondas_all, ocorrencias_all = DataProcessor.process_all_months_mode(year, filters)
        click.echo(f"   Ocorrências em junho (índice 5): {ocorrencias_all[5]}")
    except Exception as e:
        click.echo(f"   ❌ Erro: {e}")
    
    # Modo 2: Mês único
    click.echo(f"\n📊 MODO 2: MÊS ÚNICO")
    try:
        rondas_single, ocorrencias_single = DataProcessor.process_single_month_mode(year, month, filters)
        click.echo(f"   Ocorrências em junho (índice 5): {ocorrencias_single[5]}")
    except Exception as e:
        click.echo(f"   ❌ Erro: {e}")
    
    # Diferença
    diferenca = ocorrencias_all[5] - ocorrencias_single[5]
    click.echo(f"\n📊 DIFERENÇA: {diferenca} ocorrências")
    
    # Investigar o problema
    click.echo(f"\n🔍 INVESTIGANDO O PROBLEMA:")
    
    # 1. Verificar como o modo mês único calcula as datas
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    click.echo(f"   Data início (mês único): {start_date}")
    click.echo(f"   Data fim (mês único): {end_date}")
    
    # 2. Verificar como o agregador processa essas datas
    temp_filters = filters.copy()
    temp_filters["data_inicio_str"] = start_date.strftime("%Y-%m-%d")
    temp_filters["data_fim_str"] = end_date.strftime("%Y-%m-%d")
    
    click.echo(f"   Filtros temporários: {temp_filters}")
    
    # 3. Testar o agregador com os filtros do modo mês único
    click.echo(f"\n📊 TESTE DO AGREGADOR COM FILTROS DO MÊS ÚNICO:")
    try:
        ocorrencias_raw_single = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, temp_filters, is_ronda=False
        )
        click.echo(f"   Dados brutos: {ocorrencias_raw_single}")
        
        # Encontrar junho
        junho_single = None
        for mes_str, total in ocorrencias_raw_single:
            if mes_str == "2025-06":
                junho_single = total
                break
        
        click.echo(f"   Ocorrências em junho (agregador com filtros): {junho_single}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro no agregador: {e}")
    
    # 4. Testar o agregador sem filtros (como modo todos os meses)
    click.echo(f"\n📊 TESTE DO AGREGADOR SEM FILTROS:")
    try:
        ocorrencias_raw_all = DataAggregator.get_monthly_aggregation_with_filters(
            Ocorrencia, Ocorrencia.data_hora_ocorrencia, year, filters, is_ronda=False
        )
        click.echo(f"   Dados brutos: {ocorrencias_raw_all}")
        
        # Encontrar junho
        junho_all = None
        for mes_str, total in ocorrencias_raw_all:
            if mes_str == "2025-06":
                junho_all = total
                break
        
        click.echo(f"   Ocorrências em junho (agregador sem filtros): {junho_all}")
        
    except Exception as e:
        click.echo(f"   ❌ Erro no agregador: {e}")
    
    # 5. Verificar se há diferença na aplicação de filtros
    click.echo(f"\n🔍 VERIFICAÇÃO DOS FILTROS:")
    
    # Query sem filtros
    query_sem_filtros = db.session.query(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
        func.count(Ocorrencia.id)
    ).filter(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY") == str(year)
    ).group_by(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM")
    ).all()
    
    click.echo(f"   Query sem filtros: {query_sem_filtros}")
    
    # Query com filtros do modo mês único
    query_com_filtros = db.session.query(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM"), 
        func.count(Ocorrencia.id)
    )
    
    # Aplica filtros como o agregador faz
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
    
    # 6. Verificar se há ocorrências sendo excluídas pelos filtros
    click.echo(f"\n🔍 VERIFICAÇÃO DE OCORRÊNCIAS EXCLUÍDAS:")
    
    # Ocorrências que estão no modo todos os meses mas não no modo mês único
    if diferenca > 0:
        click.echo(f"   Procurando {diferenca} ocorrências que estão sendo excluídas...")
        
        # Buscar ocorrências de junho que podem estar sendo excluídas
        ocorrencias_junho = Ocorrencia.query.filter(
            func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM") == "2025-06"
        ).all()
        
        # Verificar quais estão sendo excluídas pelos filtros
        ocorrencias_excluidas = []
        for oc in ocorrencias_junho:
            # Verificar se a ocorrência passa pelos filtros do modo mês único
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
    
    # 7. Resumo e solução
    click.echo(f"\n✅ RESUMO DA INVESTIGAÇÃO:")
    click.echo(f"   • Modo 'todos os meses': {ocorrencias_all[5]} ocorrências")
    click.echo(f"   • Modo 'mês único': {ocorrencias_single[5]} ocorrências")
    click.echo(f"   • Diferença: {diferenca} ocorrências")
    
    if diferenca > 0:
        click.echo(f"\n🚨 PROBLEMA IDENTIFICADO:")
        click.echo(f"   O modo 'mês único' está aplicando filtros de data que excluem {diferenca} ocorrências")
        click.echo(f"   Isso pode estar causando a discrepância de 184 vs 188 no dashboard")
    
    logger.info(f"Investigação da discrepância no comparativo concluída. Diferença: {diferenca}")


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
    
    logger.info("Testando dashboard de ocorrências com mês específico...")
    click.echo("=== TESTE DO DASHBOARD DE OCORRÊNCIAS COM MÊS ESPECÍFICO ===")
    
    current_year = 2025
    month = 6  # Junho
    
    click.echo(f"\n📊 TESTE COM MÊS ESPECÍFICO: {month}/{current_year}")
    
    # 1. Simular como o dashboard processa o mês específico
    click.echo(f"\n🔍 SIMULAÇÃO DO DASHBOARD:")
    
    # Como o dashboard faz
    start_date_str, end_date_str = _get_date_range_from_month(current_year, month)
    click.echo(f"   Data início (dashboard): {start_date_str}")
    click.echo(f"   Data fim (dashboard): {end_date_str}")
    
    # Filtros como o dashboard aplica
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
    
    # 2. Testar o dashboard com esses filtros
    click.echo(f"\n📊 TESTE DO DASHBOARD:")
    try:
        dashboard_data = get_ocorrencia_dashboard_data(filters)
        total_dashboard = dashboard_data.get("total_ocorrencias", 0)
        click.echo(f"   Total de ocorrências (dashboard): {total_dashboard}")
    except Exception as e:
        click.echo(f"   ❌ Erro no dashboard: {e}")
        total_dashboard = 0
    
    # 3. Comparação direta
    click.echo(f"\n🔍 COMPARAÇÃO DIRETA:")
    
    # Converter strings para datetime UTC
    start_date_dt = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_date_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    
    click.echo(f"   Data início DT: {start_date_dt}")
    click.echo(f"   Data fim DT: {end_date_dt}")
    
    # Contagem direta
    total_direto = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= start_date_dt,
        Ocorrencia.data_hora_ocorrencia <= end_date_dt
    ).count()
    
    click.echo(f"   Total direto: {total_direto}")
    click.echo(f"   Diferença: {total_direto - total_dashboard}")
    
    # 4. Testar com func.to_char (como o comparativo faz)
    click.echo(f"\n📊 TESTE COM FUN.TO_CHAR:")
    
    total_func_to_char = Ocorrencia.query.filter(
        func.to_char(Ocorrencia.data_hora_ocorrencia, "YYYY-MM") == f"{current_year:04d}-{month:02d}"
    ).count()
    
    click.echo(f"   Total com func.to_char: {total_func_to_char}")
    
    # 5. Verificar se há diferença no processamento de datas
    click.echo(f"\n🔍 VERIFICAÇÃO DE PROCESSAMENTO DE DATAS:")
    
    # Como o dashboard processa as datas
    from app.utils.date_utils import parse_date_range
    date_start_range, date_end_range = parse_date_range(start_date_str, end_date_str)
    
    click.echo(f"   Date start range: {date_start_range}")
    click.echo(f"   Date end range: {date_end_range}")
    click.echo(f"   Tipo date_start_range: {type(date_start_range)}")
    click.echo(f"   Tipo date_end_range: {type(date_end_range)}")
    
    # Converter para datetime UTC como o dashboard faz
    from datetime import time
    date_start_range_dt = datetime.combine(date_start_range, time.min, tzinfo=timezone.utc)
    date_end_range_dt = datetime.combine(date_end_range, time.max, tzinfo=timezone.utc)
    
    click.echo(f"   Date start range DT: {date_start_range_dt}")
    click.echo(f"   Date end range DT: {date_end_range_dt}")
    
    # Testar com essas datas
    total_dashboard_dates = Ocorrencia.query.filter(
        Ocorrencia.data_hora_ocorrencia >= date_start_range_dt,
        Ocorrencia.data_hora_ocorrencia <= date_end_range_dt
    ).count()
    
    click.echo(f"   Total com datas do dashboard: {total_dashboard_dates}")
    
    # 6. Verificar ocorrências que podem estar sendo excluídas
    if total_direto != total_dashboard:
        click.echo(f"\n🔍 INVESTIGANDO OCORRÊNCIAS EXCLUÍDAS:")
        
        # Ocorrências que estão no nosso filtro mas não no dashboard
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
        
        # Ocorrências que estão no dashboard mas não no nosso filtro
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
    
    # 7. Resumo final
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
