# app/commands.py

import logging
import os
from datetime import timedelta

import click
from flask.cli import with_appcontext

from app.models import EscalaMensal, Ocorrencia, Ronda, User

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
