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

# --- Inicialização das Extensões (globais) ---
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

# --- Configuração de Logging ---
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger(__name__)

# --- Carregamento do .env ---
# Ajusta caminho para carregar .env da raiz do projeto (um nível acima de 'app/')
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
dotenv_path = os.path.abspath(dotenv_path)

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    module_logger.info(f".env carregado de {dotenv_path}")
    module_logger.info(f"DATABASE_URL após carregar .env: {os.getenv('DATABASE_URL')}")
else:
    module_logger.warning(f".env não encontrado em {dotenv_path}, usando variáveis de ambiente do sistema se definidas.")

# --- Fábrica de Aplicação ---
def create_app():
    app_instance = Flask(__name__)
    app_instance.wsgi_app = WhiteNoise(app_instance.wsgi_app, root='app/static/')

    # SECRET_KEY deve estar no .env para produção, senão gera aleatório
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))

    database_url_from_env = os.getenv('DATABASE_URL')
    module_logger.debug(f"DEBUG: DATABASE_URL lida pelo app: {database_url_from_env}")

    # Corrige prefixo 'postgres://' para 'postgresql://', exigência SQLAlchemy
    if database_url_from_env and database_url_from_env.startswith("postgres://"):
        database_url_from_env = database_url_from_env.replace("postgres://", "postgresql://", 1)

    # IMPORTANTÍSSIMO: NÃO usar fallback para banco local para evitar confusão
    if not database_url_from_env:
        raise RuntimeError("DATABASE_URL não definido no .env ou nas variáveis de ambiente!")

    app_instance.config['SQLALCHEMY_DATABASE_URI'] = database_url_from_env
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app_instance.config['WTF_CSRF_ENABLED'] = True
    is_production = not app_instance.debug
    app_instance.config['SESSION_COOKIE_SECURE'] = is_production
    app_instance.config['REMEMBER_COOKIE_SECURE'] = is_production
    app_instance.config['SESSION_COOKIE_HTTPONLY'] = is_production
    app_instance.config['REMEMBER_COOKIE_HTTPONLY'] = is_production

    # --- Configuração de Cache ---
    app_instance.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'RedisCache')
    app_instance.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 3600))
    app_instance.config['CACHE_REDIS_URL'] = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')

    # --- Verifica se o Redis está disponível, senão usa SimpleCache ---
    from redis.exceptions import ConnectionError
    import redis

    if app_instance.config['CACHE_TYPE'] == 'RedisCache':
        try:
            test_redis = redis.from_url(app_instance.config['CACHE_REDIS_URL'])
            test_redis.ping()
            module_logger.info("Redis conectado com sucesso.")
        except (ConnectionError, Exception) as e:
            module_logger.warning(f"Redis indisponível ({e}), caindo para SimpleCache.")
            app_instance.config['CACHE_TYPE'] = 'SimpleCache'

    # --- Inicialização das Extensões ---
    db.init_app(app_instance)
    migrate.init_app(app_instance, db)
    login_manager.init_app(app_instance)
    cache.init_app(app_instance)
    limiter.init_app(app_instance)
    csrf.init_app(app_instance)

    # --- Filtros e Processadores ---
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
        if dt_obj is None:
            return "N/A"

        local_tz = pytz.timezone('America/Sao_Paulo')

        if isinstance(dt_obj, date) and not isinstance(dt_obj, datetime):
            dt_obj = datetime(dt_obj.year, dt_obj.month, dt_obj.day)

        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)

        local_dt = dt_obj.astimezone(local_tz)
        return local_dt.strftime('%d/%m/%Y %H:%M:%S')

    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': datetime.now(timezone.utc).year}

    # --- Registro de Blueprints e CLI ---
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

        from . import commands
        app_instance.cli.add_command(commands.seed_db_command)
        app_instance.cli.add_command(commands.assign_supervisors_command)

    module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    return app_instance
