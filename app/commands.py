# app/commands.py
import click
from flask.cli import with_appcontext
from .models import User, Ronda, EscalaMensal
from . import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Cria os usuários administradores e supervisores padrão."""
    default_users = [
        {"username": "Luis Royo", "email": "luisroyo25@gmail.com", "password": "edu123cs", "is_admin": True, "is_supervisor": True},
        {"username": "Romel / Arnaldo", "email": "romel.arnaldo@example.com", "password": "password123", "is_admin": False, "is_supervisor": True},
        {"username": "Gleison", "email": "gleison@example.com", "password": "password123", "is_admin": False, "is_supervisor": True},
        {"username": "Douglas", "email": "douglas@example.com", "password": "password123", "is_admin": False, "is_supervisor": True}
    ]
    for user_data in default_users:
        try:
            user_exists = User.query.filter_by(email=user_data['email']).first()
            if not user_exists:
                new_user = User(
                    username=user_data['username'], email=user_data['email'],
                    is_admin=user_data.get('is_admin', False), is_supervisor=user_data.get('is_supervisor', False),
                    is_approved=True
                )
                new_user.set_password(user_data['password'])
                db.session.add(new_user)
                click.echo(f"Usuário '{user_data['username']}' criado com sucesso.")
            else:
                if user_data.get('is_supervisor') and not user_exists.is_supervisor:
                    user_exists.is_supervisor = True
                    click.echo(f"Usuário '{user_data['username']}' atualizado para supervisor.")
                else:
                    click.echo(f"Usuário '{user_data['username']}' já existe.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Falha ao criar/atualizar usuário '{user_data['username']}': {e}", exc_info=True)
            click.echo(f"Erro ao processar usuário '{user_data['username']}': {e}")
            return
    db.session.commit()
    click.echo("Comando de inicialização do banco de dados concluído.")


# --- COMANDO CORRIGIDO E ATUALIZADO ---
@click.command('assign-supervisors')
@click.option('--ano', type=int, help='O ano para o qual a atribuição deve ser feita (padrão: ano atual).')
@click.option('--mes', type=int, help='O mês para o qual a atribuição deve ser feita (padrão: mês atual).')
@with_appcontext
def assign_supervisors_command(ano, mes):
    """Atribui supervisores a rondas existentes com base na escala mensal definida na interface."""
    
    now = datetime.now()
    # Usa o ano e mês fornecidos, ou o padrão (mês e ano atuais)
    target_ano = ano if ano is not None else now.year
    target_mes = mes if mes is not None else now.month

    click.echo(f"Iniciando a atribuição de supervisores para rondas de {target_mes}/{target_ano}...")

    try:
        # 1. Busca a escala definida pelo usuário para o mês/ano alvo
        escalas_definidas = EscalaMensal.query.filter_by(ano=target_ano, mes=target_mes).all()
        if not escalas_definidas:
            click.echo(f"ERRO: Nenhuma escala encontrada para {target_mes}/{target_ano}. Por favor, defina a escala na página 'Gerenciar Escalas' primeiro.")
            return

        # Cria um mapa de Turno -> ID do Supervisor para fácil acesso
        mapa_escala = {escala.nome_turno: escala.supervisor_id for escala in escalas_definidas}
        click.echo(f"Escala para {target_mes}/{target_ano} carregada: {mapa_escala}")

        # 2. Busca todas as rondas daquele mês/ano
        rondas_do_periodo = Ronda.query.filter(
            db.extract('year', Ronda.data_plantao_ronda) == target_ano,
            db.extract('month', Ronda.data_plantao_ronda) == target_mes
        ).all()

        if not rondas_do_periodo:
            click.echo("Nenhuma ronda encontrada no período especificado para atualizar.")
            return

        total_updated = 0
        # 3. Itera sobre cada ronda e atribui o supervisor correto
        for ronda in rondas_do_periodo:
            supervisor_correto_id = mapa_escala.get(ronda.turno_ronda)
            
            # Atualiza apenas se o supervisor correto for encontrado na escala e for diferente do atual
            if supervisor_correto_id and ronda.supervisor_id != supervisor_correto_id:
                ronda.supervisor_id = supervisor_correto_id
                total_updated += 1
        
        # 4. Salva todas as alterações no banco de dados
        if total_updated > 0:
            db.session.commit()
            click.echo(f"\nOperação concluída! Total de {total_updated} rondas atualizadas para o período de {target_mes}/{target_ano}.")
        else:
            click.echo("\nNenhuma ronda precisou de atualização (supervisores já estavam corretos).")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Falha na atribuição em massa de supervisores: {e}", exc_info=True)
        click.echo(f"ERRO: A operação falhou e foi revertida. Detalhes: {e}")