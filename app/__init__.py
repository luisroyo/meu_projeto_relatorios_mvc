import os
import logging
from datetime import datetime as dt, timezone # << ADICIONADO timezone AQUI
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
    
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'site.db')
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_FLASK', default_db_path)
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    module_logger.info(f"Banco de dados URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app_instance)
    module_logger.info("SQLAlchemy inicializado com a app.")
    migrate.init_app(app_instance, db)
    module_logger.info("Flask-Migrate inicializado com a app.")
    login_manager.init_app(app_instance)
    module_logger.info("Flask-Login inicializado com a app.")
    
    if not app_instance.logger.handlers or os.environ.get("FLASK_ENV") == "development":
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        if not any(isinstance(h, logging.StreamHandler) for h in app_instance.logger.handlers):
             app_instance.logger.addHandler(stream_handler)
        
        app_instance.logger.setLevel(log_level)
        
        module_logger.info(f"Configuração de logging aplicada. Nível: {log_level_str}")
        app_instance.logger.info("Logger da aplicação Flask configurado.")

    with app_instance.app_context():
        from . import models 
        module_logger.info("Modelos importados no contexto da app.")

        # --- CÓDIGO TEMPORÁRIO PARA CRIAR ADMIN NO RENDER ---
        # (Mantido como estava, mas note que ele não criou 'du@du.com' devido ao admin existente)
        admin_exists = models.User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            app_instance.logger.info("Nenhum administrador encontrado. Tentando criar admin padrão...")
            try:
                admin_email = "du@du.com"
                admin_username = "du" 
                admin_password = "123" 

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
            # Log modificado para ser mais claro
            app_instance.logger.info(f"Verificação de admin: Um administrador ('{admin_exists.username}') já existe. Nenhum novo admin padrão foi criado.")
        # --- FIM DO CÓDIGO TEMPORÁRIO ---

        from .routes import main_bp
        app_instance.register_blueprint(main_bp)
        module_logger.info(f"Blueprint '{main_bp.name}' registrado.")

    @app_instance.context_processor
    def inject_current_year():
        # CORRIGIDO: Usa timezone importado diretamente
        return {'SCRIPT_CURRENT_YEAR': dt.now(timezone.utc).year}
    
    module_logger.info("Aplicação Flask completamente configurada e pronta.")
    return app_instance
