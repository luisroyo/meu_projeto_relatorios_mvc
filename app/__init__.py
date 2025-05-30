# app/__init__.py
import os
import logging
from datetime import datetime as dt, timezone
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Carrega variáveis de ambiente do .env na raiz do projeto, se existir
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Defina as instâncias das extensões AQUI, no nível do módulo
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Configure o login_manager AQUI
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Configuração básica de logging para o módulo (logger raiz)
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

module_logger = logging.getLogger(__name__)

# Log do carregamento do .env (acontecerá em ambos os processos do reloader, o que é normal)
if os.path.exists(dotenv_path):
    module_logger.info(f".env carregado de {dotenv_path}")
else:
    module_logger.info(f".env não encontrado em {dotenv_path}, usando variáveis de ambiente do sistema se definidas.")


def create_app():
    app_instance = Flask(__name__)

    # Configurações da Aplicação
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'site.db')
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_FLASK', default_db_path)
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app_instance.config['WTF_CSRF_ENABLED'] = True

    # Determinar o contexto de execução para controlar logs detalhados de inicialização e config do app.logger
    is_werkzeug_main_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    # Consideramos "não debug" se FLASK_DEBUG não estiver explicitamente '1', 'true', ou 'on'
    is_not_flask_debug_mode = str(os.getenv('FLASK_DEBUG', '0')).lower() not in ['1', 'true', 'on']
    
    # Logar detalhes/configurar app.logger se (é o processo filho do reloader) OU (não é modo debug do Flask explícito)
    should_perform_single_run_actions = is_werkzeug_main_process or is_not_flask_debug_mode

    if should_perform_single_run_actions:
        module_logger.info("Instância Flask criada.")

    instance_path = os.path.join(BASE_DIR, 'instance')
    if not os.path.exists(instance_path) and 'sqlite:///' in app_instance.config['SQLALCHEMY_DATABASE_URI']:
        try:
            os.makedirs(instance_path)
            if should_perform_single_run_actions:
                 module_logger.info(f"Diretório 'instance' criado em {instance_path}")
        except OSError as e:
            module_logger.error(f"Erro ao criar diretório 'instance': {e}")

    if should_perform_single_run_actions:
        module_logger.info(f"Banco de dados URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("SQLAlchemy inicializado com a app.")
    
    migrate.init_app(app_instance, db)
    if should_perform_single_run_actions: module_logger.info("Flask-Migrate inicializado com a app.")
    
    login_manager.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("Flask-Login inicializado com a app.")
    
    csrf.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("CSRFProtect inicializado com a app.")
    
    # Configuração de Logging da Aplicação Flask (para app_instance.logger)
    if should_perform_single_run_actions:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if app_instance.logger.hasHandlers():
            app_instance.logger.handlers.clear()

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        app_instance.logger.addHandler(stream_handler)
        app_instance.logger.setLevel(log_level)
        
        module_logger.info(f"Configuração de logging da aplicação Flask (app.logger) aplicada. Nível: {log_level_str}")
        app_instance.logger.info("Logger da aplicação Flask (app.logger) configurado e pronto.")


    with app_instance.app_context():
        from . import models 
        if should_perform_single_run_actions: module_logger.info("Modelos importados no contexto da app.")

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
        app_instance.register_blueprint(ronda_bp) 
        if should_perform_single_run_actions: module_logger.info(f"Blueprint '{ronda_bp.name}' registrado com prefixo '{ronda_bp.url_prefix}'.")

    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': dt.now(timezone.utc).year}
    
    if should_perform_single_run_actions:
        module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    
    return app_instance