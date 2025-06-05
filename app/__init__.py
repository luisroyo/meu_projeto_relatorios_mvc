# app/__init__.py
import os
import logging
from datetime import datetime as dt, timezone
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
# from app.models import User # <--- REMOVA OU COMENTE ESTA LINHA (causa do erro circular)
from werkzeug.security import generate_password_hash # Pode ser necessário se User.set_password não for chamado

# Defina as instâncias das extensões AQUI, no nível do módulo
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Configure o login_manager AQUI
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

module_logger = logging.getLogger(__name__)

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    module_logger.info(f".env carregado de {dotenv_path}")
else:
    module_logger.info(f".env não encontrado em {dotenv_path}, usando variáveis de ambiente do sistema se definidas.")


def create_app():
    app_instance = Flask(__name__)
    # Removido log de criação de instância daqui para evitar duplicidade se create_app for chamada várias vezes por engano
    
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'site.db')
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_FLASK', default_db_path)
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app_instance.config['WTF_CSRF_ENABLED'] = True

    is_werkzeug_main_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    is_not_flask_debug_mode = str(os.getenv('FLASK_DEBUG', '0')).lower() not in ['1', 'true', 'on']
    should_perform_single_run_actions = is_werkzeug_main_process or is_not_flask_debug_mode
    
    if should_perform_single_run_actions:
        module_logger.info("create_app: Instância Flask criada e configurações básicas aplicadas.")
        module_logger.info(f"Banco de dados URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("SQLAlchemy inicializado com a app.")
    
    migrate.init_app(app_instance, db)
    if should_perform_single_run_actions: module_logger.info("Flask-Migrate inicializado com a app.")
    
    login_manager.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("Flask-Login inicializado com a app.")
    
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("CSRFProtect inicializado com a app.")

    if should_perform_single_run_actions:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        if not app_instance.logger.handlers or app_instance.logger.name == 'flask.app': # Evita reconfigurar se já configurado por Flask
            # Se for o logger padrão do Flask 'flask.app', ele pode já ter handlers.
            # Se for um logger customizado ou se não tiver handlers, configuramos.
            if app_instance.logger.hasHandlers():
                 app_instance.logger.handlers.clear()

            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            app_instance.logger.addHandler(stream_handler)
            app_instance.logger.setLevel(log_level)
            app_instance.logger.propagate = False 
            module_logger.info(f"Configuração de logging da aplicação Flask (app.logger) aplicada. Nível: {log_level_str}")
        # Removido o segundo log "Logger da aplicação Flask (app.logger) configurado e pronto." para evitar duplicidade.

    with app_instance.app_context():
        from . import models # Esta importação é a correta e permanece aqui
        if should_perform_single_run_actions: module_logger.info("Modelos importados no contexto da app.")

        # --- CÓDIGO TEMPORÁRIO PARA CRIAR USUÁRIO ADMINISTRADOR ---
        # !!! IMPORTANTE: REMOVA ESTE BLOCO DE CÓDIGO APÓS O USUÁRIO SER CRIADO E TESTADO !!!
        admin_email_to_create = "luisroyo25@gmail.com"
        admin_username_to_create = "Luis Royo"
        admin_password_to_create = "edu123cs"

        # Verifica se o usuário já existe para evitar erro de duplicação
        existing_admin = models.User.query.filter_by(email=admin_email_to_create).first()
        if not existing_admin:
            if should_perform_single_run_actions: # Loga apenas uma vez
                module_logger.info(f"Usuário administrador {admin_email_to_create} não encontrado, tentando criar...")
            try:
                admin_user = models.User(
                    username=admin_username_to_create,
                    email=admin_email_to_create,
                    is_admin=True,
                    is_approved=True 
                )
                admin_user.set_password(admin_password_to_create) 
                db.session.add(admin_user)
                db.session.commit()
                if should_perform_single_run_actions: # Loga apenas uma vez
                    module_logger.info(f"Usuário administrador {admin_email_to_create} criado com sucesso.")
            except Exception as e:
                db.session.rollback()
                module_logger.error(f"Falha ao criar usuário administrador {admin_email_to_create}: {e}", exc_info=True)
        else:
            if should_perform_single_run_actions: # Loga apenas uma vez
                module_logger.info(f"Usuário administrador {admin_email_to_create} já existe. Nenhuma ação tomada.")
        # --- FIM DO CÓDIGO TEMPORÁRIO ---

        from app.blueprints.main.routes import main_bp
        app_instance.register_blueprint(main_bp)
        if should_perform_single_run_actions: module_logger.info(f"Blueprint '{main_bp.name}' registrado.")

        from app.blueprints.auth.routes import auth_bp
        app_instance.register_blueprint(auth_bp)
        if should_perform_single_run_actions: module_logger.info(f"Blueprint '{auth_bp.name}' registrado.")

        from app.blueprints.admin.routes import admin_bp
        app_instance.register_blueprint(admin_bp) 
        if should_perform_single_run_actions: module_logger.info(f"Blueprint '{admin_bp.name}' registrado com prefixo '{admin_bp.url_prefix}'.")

        from app.blueprints.ronda.routes import ronda_bp
        app_instance.register_blueprint(ronda_bp, url_prefix='/ronda') 
        if should_perform_single_run_actions: module_logger.info(f"Blueprint '{ronda_bp.name}' registrado com prefixo '/ronda'.")


    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': dt.now(timezone.utc).year}
    
    if should_perform_single_run_actions:
        module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    
    return app_instance