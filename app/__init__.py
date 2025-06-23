import os
import logging
from datetime import datetime as dt, timezone
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import pytz
from whitenoise import WhiteNoise

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

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

    app_instance.wsgi_app = WhiteNoise(app_instance.wsgi_app, root='app/static/')

    # --- Configurações da Aplicação ---
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'site.db')
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_FLASK', default_db_path)
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # --- Configurações de CSRF e Cookies ---
    app_instance.config['WTF_CSRF_ENABLED'] = True
    
    # Em um ambiente de produção real, app_instance.debug deve ser False
    is_production = not app_instance.debug
    app_instance.config['SESSION_COOKIE_SECURE'] = is_production
    app_instance.config['REMEMBER_COOKIE_SECURE'] = is_production
    app_instance.config['SESSION_COOKIE_HTTPONLY'] = is_production
    app_instance.config['REMEMBER_COOKIE_HTTPONLY'] = is_production

    # --- Configuração de Cache ---
    app_instance.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'RedisCache')
    app_instance.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 3600))
    app_instance.config['CACHE_REDIS_URL'] = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    
    # --- Inicialização das Extensões ---
    db.init_app(app_instance)
    migrate.init_app(app_instance, db)
    login_manager.init_app(app_instance)
    cache.init_app(app_instance)
    limiter.init_app(app_instance)
    csrf.init_app(app_instance)
    
    # --- Definição de Filtros de Template ---
    @app_instance.template_filter('localtime')
    def localtime_filter(dt_obj):
        if dt_obj is None:
            return "N/A"
        local_tz = pytz.timezone('America/Sao_Paulo')
        
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
            
        local_dt = dt_obj.astimezone(local_tz)
        return local_dt.strftime('%d/%m/%Y %H:%M:%S')

    # --- Registro de Blueprints e Comandos ---
    with app_instance.app_context():
        from . import models # Importar models para que SQLAlchemy possa encontrá-los
        from app.blueprints.main.routes import main_bp
        app_instance.register_blueprint(main_bp)
        from app.blueprints.auth.routes import auth_bp
        app_instance.register_blueprint(auth_bp)
        from app.blueprints.admin import admin_bp
        app_instance.register_blueprint(admin_bp, url_prefix='/admin')
        from app.blueprints.ronda.routes import ronda_bp
        app_instance.register_blueprint(ronda_bp, url_prefix='/ronda')

    from . import commands
    # REMOVIDO: app_instance.cli.add_command(commands.seed_db_command)
    # REMOVIDO: app_instance.cli.add_command(commands.assign_supervisors_command)
    # NOVO: Chamar a função init_app de commands para registrar todos os comandos
    commands.init_app(app_instance) # CORREÇÃO APLICADA AQUI

    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': dt.now(timezone.utc).year}
    
    module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    
    return app_instance