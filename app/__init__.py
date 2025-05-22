import os
import logging
# import datetime # datetime do módulo datetime é necessário para context_processor
from datetime import datetime as dt # Renomeado para evitar conflito com módulo datetime
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Carrega variáveis de ambiente do .env na raiz do projeto, se existir
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logging.info(f".env carregado de {dotenv_path}")
else:
    logging.info(f".env não encontrado em {dotenv_path}, usando variáveis de ambiente do sistema se definidas.")


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

module_logger = logging.getLogger(__name__)

def create_app():
    app_instance = Flask(__name__)
    module_logger.info("Instância Flask criada.")

    # Configurações da Aplicação
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    
    # Determina o diretório base do projeto (um nível acima de 'app')
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Configuração do Banco de Dados
    default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'site.db')
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_FLASK', default_db_path) # Use DATABASE_URL_FLASK para Render
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    module_logger.info(f"Banco de dados URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")

    # Inicialização das Extensões
    db.init_app(app_instance)
    module_logger.info("SQLAlchemy inicializado com a app.")
    migrate.init_app(app_instance, db)
    module_logger.info("Flask-Migrate inicializado com a app.")
    login_manager.init_app(app_instance)
    module_logger.info("Flask-Login inicializado com a app.")
    
    # Configuração de Logging
    # A configuração de logging foi movida para ser mais robusta e evitar duplicação
    # com o reloader do Werkzeug ou quando executado por Gunicorn/WSGI.
    if not app_instance.logger.handlers or os.environ.get("FLASK_ENV") == "development": # Configura se não houver handlers ou em dev
        # Define o nível do logger da app
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Remove handlers existentes para evitar duplicação se a factory for chamada múltiplas vezes
        # (embora com `if not app_instance.logger.handlers` isso seja menos provável)
        # while app_instance.logger.handlers:
        #     app_instance.logger.removeHandler(app_instance.logger.handlers[0])

        # Handler para console (stdout)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        # Adiciona o handler ao logger da app
        if not any(isinstance(h, logging.StreamHandler) for h in app_instance.logger.handlers):
             app_instance.logger.addHandler(stream_handler)
        
        app_instance.logger.setLevel(log_level)
        
        # Configura o logger raiz também, se necessário, ou apenas o logger da app.
        # logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', force=True)
        
        module_logger.info(f"Configuração de logging aplicada. Nível: {log_level_str}")
        app_instance.logger.info("Logger da aplicação Flask configurado.")


    # Importa modelos e registra blueprints dentro do contexto da aplicação
    with app_instance.app_context():
        from . import models # Importa os modelos para que sejam conhecidos pelo SQLAlchemy
        module_logger.info("Modelos importados no contexto da app.")

        # --- CÓDIGO TEMPORÁRIO PARA CRIAR ADMIN NO RENDER ---
        # Este bloco deve ser executado dentro do contexto da aplicação
        # Verifique se já existe algum administrador
        admin_exists = models.User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            app_instance.logger.info("Nenhum administrador encontrado. Tentando criar admin padrão...")
            try:
                admin_email = "du@du.com"
                admin_username = "du" # Username baseado no email
                admin_password = "123" # SENHA FORNECIDA PELO USUÁRIO

                existing_user_by_email = models.User.query.filter_by(email=admin_email).first()
                existing_user_by_username = models.User.query.filter_by(username=admin_username).first()

                if existing_user_by_email:
                    app_instance.logger.info(f"Usuário com email {admin_email} já existe. Verificando se é admin...")
                    if not existing_user_by_email.is_admin:
                        existing_user_by_email.is_admin = True
                        existing_user_by_email.is_approved = True
                        db.session.commit()
                        app_instance.logger.info(f"Usuário {existing_user_by_email.username} promovido a admin.")
                    else:
                        app_instance.logger.info(f"Usuário {existing_user_by_email.username} já é admin.")
                elif existing_user_by_username:
                    app_instance.logger.info(f"Usuário com username {admin_username} já existe (email diferente). Verificando se é admin...")
                    if not existing_user_by_username.is_admin:
                        existing_user_by_username.is_admin = True
                        existing_user_by_username.is_approved = True
                        db.session.commit()
                        app_instance.logger.info(f"Usuário {existing_user_by_username.username} promovido a admin.")
                    else:
                        app_instance.logger.info(f"Usuário {existing_user_by_username.username} já é admin.")
                else:
                    default_admin = models.User(username=admin_username, email=admin_email)
                    default_admin.set_password(admin_password)
                    default_admin.is_admin = True
                    default_admin.is_approved = True
                    db.session.add(default_admin)
                    db.session.commit()
                    app_instance.logger.info(f"Administrador padrão '{default_admin.username}' criado com sucesso.")
            except Exception as e:
                app_instance.logger.error(f"Erro ao tentar criar administrador padrão: {e}", exc_info=True)
                db.session.rollback()
        else:
            app_instance.logger.info(f"Administrador já existe: {admin_exists.username}")
        # --- FIM DO CÓDIGO TEMPORÁRIO ---

        from .routes import main_bp
        app_instance.register_blueprint(main_bp)
        module_logger.info(f"Blueprint '{main_bp.name}' registrado.")

    @app_instance.context_processor
    def inject_current_year():
        # Use o dt importado para evitar conflito com o módulo datetime
        return {'SCRIPT_CURRENT_YEAR': dt.now(dt.timezone.utc).year}
    
    module_logger.info("Aplicação Flask completamente configurada e pronta.")
    return app_instance
