# app/commands.py
import click
from flask.cli import with_appcontext
from .models import User  # Importa seus modelos
from . import db         # Importa a instância db de app/__init__.py
import logging

# Você pode usar o logger da app atual ou um logger de módulo
# from flask import current_app
# logger = current_app.logger
logger = logging.getLogger(__name__)


@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Cria o usuário administrador padrão se ele não existir."""
    admin_email_to_create = "luisroyo25@gmail.com"
    admin_username_to_create = "Luis Royo"
    admin_password_to_create = "edu123cs" # Considere usar variáveis de ambiente para isso

    try:
        existing_admin = User.query.filter_by(email=admin_email_to_create).first()
        if not existing_admin:
            logger.info(f"Usuário administrador {admin_email_to_create} não encontrado, criando...")
            admin_user = User(
                username=admin_username_to_create,
                email=admin_email_to_create,
                is_admin=True,
                is_approved=True  # Ativa o usuário imediatamente
            )
            admin_user.set_password(admin_password_to_create) # A função set_password faz o hash
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"Usuário administrador {admin_email_to_create} criado com sucesso.")
            click.echo(f"Usuário administrador {admin_email_to_create} criado com sucesso.")
        else:
            logger.info(f"Usuário administrador {admin_email_to_create} já existe.")
            click.echo(f"Usuário administrador {admin_email_to_create} já existe.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Falha ao criar usuário administrador {admin_email_to_create}: {e}", exc_info=True)
        click.echo(f"Erro ao criar usuário administrador: {e}")

# Você pode adicionar outros comandos aqui no futuro