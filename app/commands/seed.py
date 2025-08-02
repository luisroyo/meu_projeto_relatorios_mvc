import logging
import os
import click
from flask.cli import with_appcontext
from app.models import User
from app import db

logger = logging.getLogger(__name__)

@click.command("seed-db")
@with_appcontext
def seed_db_command():
    """
    Cria usuários administradores e supervisores padrão para desenvolvimento.
    AVISO: Nunca use este comando em produção! As senhas são fracas e conhecidas.
    Para produção, crie usuários manualmente ou implemente um fluxo seguro.
    """
    default_users = [
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
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    is_admin=user_data.get("is_admin", False),
                    is_supervisor=user_data.get("is_supervisor", False),
                    is_approved=user_data.get("is_approved", True),
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

@click.command("seed-condominios")
@with_appcontext
def seed_condominios_command():
    """Cria condomínios de exemplo para o sistema de rondas."""
    from app.models.condominio import Condominio
    
    condominios_exemplo = [
        "ZERMATT",
        "RESIDENCIAL VILLA VERDE",
        "CONDOMÍNIO SOLAR",
        "RESIDENCIAL PARQUE DAS FLORES",
        "CONDOMÍNIO VISTA ALEGRE",
        "RESIDENCIAL JARDIM BOTÂNICO",
        "CONDOMÍNIO MORADA NOBRE",
        "RESIDENCIAL VALE DO SOL"
    ]
    
    for nome in condominios_exemplo:
        # Verifica se já existe
        condominio_existente = Condominio.query.filter_by(nome=nome).first()
        if not condominio_existente:
            condominio = Condominio(nome=nome)
            db.session.add(condominio)
            click.echo(f"✅ Condomínio '{nome}' criado")
        else:
            click.echo(f"⏭️  Condomínio '{nome}' já existe")
    
    db.session.commit()
    click.echo("🎉 Condomínios de exemplo criados com sucesso!") 