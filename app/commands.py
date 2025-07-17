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
