# app/__init__.py (VERSÃO CORRIGIDA)

import os
import logging
from datetime import datetime
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
from config import DevelopmentConfig  # <-- Importa a configuração padrão

# --- Instancia as extensões ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
    # A URL de armazenamento será carregada a partir da configuração do app
)

# --- Configura o LoginManager ---
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# --- Configura o Logging ---
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger(__name__)


# --- Fábrica da Aplicação ---
def create_app(config_class=DevelopmentConfig): # <-- 1. Aceita uma classe de configuração como argumento
    """Cria e configura a aplicação Flask."""
    app_instance = Flask(__name__)

    # 2. Carrega a configuração a partir do objeto fornecido
    # Isto substitui todo o bloco de carregamento manual do .env e os os.getenv()
    app_instance.config.from_object(config_class)

    # Inicializa as extensões com a instância da aplicação
    db.init_app(app_instance)
    migrate.init_app(app_instance, db)
    login_manager.init_app(app_instance)
    cache.init_app(app_instance)
    limiter.init_app(app_instance)
    csrf.init_app(app_instance)
    
    # Adiciona o WhiteNoise para servir arquivos estáticos
    app_instance.wsgi_app = WhiteNoise(app_instance.wsgi_app, root='app/static/')

    # --- Registros e Lógica dentro do contexto da aplicação ---
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        try:
            return db.session.get(User, int(user_id))
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
        # Registra os Blueprints
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
        
        # Registra os Comandos de CLI
        from . import commands
        app_instance.cli.add_command(commands.seed_db_command)
        app_instance.cli.add_command(commands.assign_supervisors_command)

    module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    return app_instance