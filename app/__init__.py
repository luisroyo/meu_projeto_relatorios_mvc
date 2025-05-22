from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # Endpoint da sua rota de login (ajuste se o blueprint for diferente)
login_manager.login_message_category = 'info'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

def setup_logging(app):
    # ... (seu código de setup de logging existente)
    # Garanta que current_app.logger funcione ou use logging.getLogger(__name__)
    pass # Remova este pass e coloque seu código de logging aqui

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configura o logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicação iniciada') # Exemplo de log

    # Inicializa as extensões com a app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importa os modelos AQUI para que db esteja associado à app
    # e para que o código de setup abaixo possa usá-los.
    from app.models import User # Certifique-se que User está definido em app.models

    # --- CÓDIGO TEMPORÁRIO PARA CRIAR ADMIN NO RENDER ---
    # Este bloco deve ser executado dentro do contexto da aplicação
    with app.app_context():
        # Verifique se já existe algum administrador
        admin_exists = User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            app.logger.info("Nenhum administrador encontrado. Tentando criar admin padrão para o Render...")
            try:
                # Verifique se o usuário específico já existe (pelo email, por exemplo)
                # para evitar tentar criar duplicatas se o código rodar mais de uma vez
                # antes de ser removido.
                admin_email = "du@du.com" # << MUDE ISSO!
                admin_username = "dududu" # << MUDE ISSO!
                admin_password = "123456" # << MUDE ISSO E GUARDE BEM!

                existing_user_by_email = User.query.filter_by(email=admin_email).first()
                existing_user_by_username = User.query.filter_by(username=admin_username).first()

                if existing_user_by_email:
                    app.logger.info(f"Usuário com email {admin_email} já existe. Verificando se é admin...")
                    if not existing_user_by_email.is_admin:
                        existing_user_by_email.is_admin = True
                        existing_user_by_email.is_approved = True # Garanta que está aprovado
                        db.session.commit()
                        app.logger.info(f"Usuário {existing_user_by_email.username} promovido a admin.")
                    else:
                        app.logger.info(f"Usuário {existing_user_by_email.username} já é admin.")

                elif existing_user_by_username:
                    # Menos provável se o email for único, mas uma checagem extra
                    app.logger.info(f"Usuário com username {admin_username} já existe (email diferente). Verificando se é admin...")
                    if not existing_user_by_username.is_admin:
                        existing_user_by_username.is_admin = True
                        existing_user_by_username.is_approved = True
                        db.session.commit()
                        app.logger.info(f"Usuário {existing_user_by_username.username} promovido a admin.")
                    else:
                        app.logger.info(f"Usuário {existing_user_by_username.username} já é admin.")
                else:
                    # Cria o novo administrador
                    default_admin = User(username=admin_username, email=admin_email)
                    default_admin.set_password(admin_password)
                    default_admin.is_admin = True
                    default_admin.is_approved = True # Admin deve ser aprovado
                    db.session.add(default_admin)
                    db.session.commit()
                    app.logger.info(f"Administrador padrão '{default_admin.username}' criado com sucesso no Render.")
            except Exception as e:
                app.logger.error(f"Erro ao tentar criar administrador padrão no Render: {e}")
                db.session.rollback() # Importante em caso de erro
    # --- FIM DO CÓDIGO TEMPORÁRIO ---

    # Importa e registra os Blueprints
    from app.routes import main_bp # Supondo que seu blueprint se chama main_bp
    app.register_blueprint(main_bp)
    app.logger.info(f"Blueprint '{main_bp.name}' registrado.")

    app.logger.info("Aplicação Flask completamente configurada e pronta.")
    return app