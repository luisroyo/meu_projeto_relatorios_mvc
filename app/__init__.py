# app/__init__.py
import os
import logging
from datetime import datetime as dt, timezone
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import pytz # <-- NOVA IMPORTAÇÃO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

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
    migrate.init_app(app_instance, db)
    login_manager.init_app(app_instance)
    
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app_instance)

    if should_perform_single_run_actions:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        if not app_instance.logger.handlers or app_instance.logger.name == 'flask.app':
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

    # --- NOVO FILTRO DE TEMPLATE PARA FUSO HORÁRIO ---
    @app_instance.template_filter('localtime')
    def localtime_filter(dt_obj):
        """Converte um datetime UTC para o fuso horário de São Paulo."""
        if dt_obj is None:
            return "N/A"
        
        utc_tz = pytz.timezone('UTC')
        local_tz = pytz.timezone('America/Sao_Paulo')
        
        # Assume que o objeto datetime do banco de dados é 'naive' mas representa UTC
        aware_utc_dt = utc_tz.localize(dt_obj)
        
        # Converte para o fuso horário local do Brasil
        local_dt = aware_utc_dt.astimezone(local_tz)
        
        return local_dt.strftime('%d/%m/%Y %H:%M:%S')
    # --- FIM DO NOVO FILTRO ---

    with app_instance.app_context():
        from . import models
        if should_perform_single_run_actions: module_logger.info("Modelos importados no contexto da app.")

        from app.blueprints.main.routes import main_bp
        app_instance.register_blueprint(main_bp)
        
        from app.blueprints.auth.routes import auth_bp
        app_instance.register_blueprint(auth_bp)
        
        from app.blueprints.admin.routes import admin_bp
        app_instance.register_blueprint(admin_bp) 
        
        from app.blueprints.ronda.routes import ronda_bp
        app_instance.register_blueprint(ronda_bp, url_prefix='/ronda') 

    # Registrar comandos CLI customizados
    from . import commands
    app_instance.cli.add_command(commands.create_admin_command)
    if should_perform_single_run_actions: module_logger.info("Comandos CLI customizados registrados.")

    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': dt.now(timezone.utc).year}
    
    if should_perform_single_run_actions:
        module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    
    return app_instance