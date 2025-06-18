# app/commands.py
import click
from flask.cli import with_appcontext
from .models import User
from . import db
import logging
import re

logger = logging.getLogger(__name__)

# O comando foi renomeado de 'create-admin' para 'seed-db' para refletir sua nova função
@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Cria os usuários administradores e supervisores padrão."""
    
    # Lista de todos os usuários padrão que queremos garantir que existam
    default_users = [
        {
            "username": "Luis Royo",
            "email": "luisroyo25@gmail.com",
            "password": "edu123cs", # Considere usar uma variável de ambiente
            "is_admin": True,
            "is_supervisor": True # Admins também podem ser supervisores
        },
        {
            "username": "Romel / Arnaldo",
            "email": "romel.arnaldo@example.com", # Email de exemplo
            "password": "password123",
            "is_admin": False,
            "is_supervisor": True
        },
        {
            "username": "Gleison",
            "email": "gleison@example.com", # Email de exemplo
            "password": "password123",
            "is_admin": False,
            "is_supervisor": True
        },
        {
            "username": "Douglas",
            "email": "douglas@example.com", # Email de exemplo
            "password": "password123",
            "is_admin": False,
            "is_supervisor": True
        }
    ]

    for user_data in default_users:
        try:
            user_exists = User.query.filter_by(email=user_data['email']).first()
            if not user_exists:
                new_user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    is_admin=user_data.get('is_admin', False),
                    is_supervisor=user_data.get('is_supervisor', False),
                    is_approved=True  # Aprova todos os usuários padrão automaticamente
                )
                new_user.set_password(user_data['password'])
                db.session.add(new_user)
                logger.info(f"Usuário '{user_data['username']}' criado com sucesso.")
                click.echo(f"Usuário '{user_data['username']}' criado com sucesso.")
            else:
                # Se o usuário já existe, podemos garantir que ele tenha o status correto
                if user_data['is_supervisor'] and not user_exists.is_supervisor:
                    user_exists.is_supervisor = True
                    logger.info(f"Usuário '{user_data['username']}' atualizado para supervisor.")
                    click.echo(f"Usuário '{user_data['username']}' atualizado para supervisor.")
                else:
                    logger.info(f"Usuário '{user_data['username']}' já existe.")
                    click.echo(f"Usuário '{user_data['username']}' já existe.")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Falha ao criar/atualizar usuário '{user_data['username']}': {e}", exc_info=True)
            click.echo(f"Erro ao processar usuário '{user_data['username']}': {e}")
            # Interrompe o processo se um usuário falhar
            return

    db.session.commit()
    logger.info("Comando seed-db concluído com sucesso.")
    click.echo("Comando de inicialização do banco de dados concluído.")