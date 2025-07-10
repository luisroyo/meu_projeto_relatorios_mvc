# app/__init__.py

import os
import logging
from datetime import datetime, date, timezone
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
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')
)

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger(__name__)

def create_app():
    app_instance = Flask(__name__)
    dotenv_path = os.path.join(os.path.dirname(app_instance.root_path), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        module_logger.info(f".env carregado de {dotenv_path}")

    app_instance.wsgi_app = WhiteNoise(app_instance.wsgi_app, root='app/static/')
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key')
    database_url_from_env = os.getenv('DATABASE_URL')
    if database_url_from_env and database_url_from_env.startswith("postgres://"):
        database_url_from_env = database_url_from_env.replace("postgres://", "postgresql://", 1)
    if not database_url_from_env:
        raise RuntimeError("DATABASE_URL não definido no .env ou nas variáveis de ambiente!")
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = database_url_from_env
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app_instance.config['WTF_CSRF_ENABLED'] = True
    
    app_instance.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'SimpleCache')
    
    db.init_app(app_instance)
    migrate.init_app(app_instance, db)
    login_manager.init_app(app_instance)
    cache.init_app(app_instance)
    limiter.init_app(app_instance)
    csrf.init_app(app_instance)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        try: return db.session.get(User, int(user_id))
        except Exception as e:
            module_logger.error(f"Erro ao carregar usuário {user_id}: {e}")
            return None

    @app_instance.template_filter('localtime')
    def localtime_filter(dt_obj):
        if dt_obj is None: return "N/A"
        local_tz = pytz.timezone('America/Sao_Paulo')
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        local_dt = dt_obj.astimezone(local_tz)
        return local_dt.strftime('%d/%m/%Y %H:%M:%S')

    @app_instance.template_filter('format_for_input')
    def format_for_input_filter(dt_obj):
        if dt_obj is None: return ""
        local_tz = pytz.timezone('America/Sao_Paulo')
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        local_dt = dt_obj.astimezone(local_tz)
        return local_dt.strftime('%Y-%m-%dT%H:%M')

    with app_instance.app_context():
        from . import models
        from app.blueprints.main.routes import main_bp
        app_instance.register_blueprint(main_bp)
        from app.blueprints.auth.routes import auth_bp
        app_instance.register_blueprint(auth_bp)
        from app.blueprints.admin import admin_bp
        app_instance.register_blueprint(admin_bp, url_prefix='/admin')
        from app.blueprints.ronda.routes import ronda_bp
        app_instance.register_blueprint(ronda_bp)
        from app.blueprints.ocorrencia.routes import ocorrencia_bp
        app_instance.register_blueprint(ocorrencia_bp)
        
        # --- CORREÇÃO: Registrando todos os comandos ---
        from . import commands
        app_instance.cli.add_command(commands.seed_db_command)
        app_instance.cli.add_command(commands.assign_supervisors_command)         # --- REGISTRO DO NOVO COMANDO DE CORREÇÃO ---
        app_instance.cli.add_command(commands.fix_ocorrencias_definitive_command) # <-- REGISTRO DO COMANDO FINAL

    module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    return app_instance
