# app/__init__.py (VERSÃO CORRIGIDA)

import logging
import os
from logging.handlers import RotatingFileHandler

import pytz
from flask import Flask
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from whitenoise import WhiteNoise
from flask_cors import CORS

# Carrega variáveis de ambiente do arquivo .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Se python-dotenv não estiver instalado, continua sem carregar .env
    pass

from config import DevelopmentConfig  # <-- Importa a configuração padrão

# --- Instancia as extensões ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()
# Use a URL do Redis de variável de ambiente, ou padrão para memory:// se não definida
redis_url = os.environ.get("REDIS_URL", "memory://")
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=redis_url
)

# --- Configura o LoginManager ---
# A configuração de login_view deve ser feita após a criação do app

# --- Configura o Logging ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
module_logger = logging.getLogger(__name__)

# Log rotation para arquivo de log principal
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "assistente_ia_seg.log")
file_handler = RotatingFileHandler(
    log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s"
    )
)
file_handler.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logging.getLogger().addHandler(file_handler)

# ATENÇÃO: Nunca logue dados sensíveis (senhas, tokens, dados pessoais)!


# --- Fábrica da Aplicação ---
def create_app(
    config_class=DevelopmentConfig,
):  # <-- 1. Aceita uma classe de configuração como argumento
    """Cria e configura a aplicação Flask."""
    app_instance = Flask(__name__)

    # Habilita CORS para rotas /api/*, /ocorrencias/* e /login
    CORS(
        app_instance,
        resources={
            r"/api/*": {"origins": ["http://localhost:8081", "*"]},
            r"/ocorrencias/*": {"origins": ["http://localhost:8081", "*"]},
            r"/login": {"origins": ["http://localhost:8081", "*"]}
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        expose_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

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

    # Configura o login_view após o init_app
    login_manager.login_view = "auth.login"  # type: ignore
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    # Adiciona o WhiteNoise para servir arquivos estáticos
    app_instance.wsgi_app = WhiteNoise(app_instance.wsgi_app, root="app/static/")

    # --- Registros e Lógica dentro do contexto da aplicação ---
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User

        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            module_logger.error(f"Erro ao carregar usuário {user_id}: {e}")
            return None

    @app_instance.template_filter("localtime")
    def localtime_filter(dt_obj):
        if dt_obj is None:
            return "N/A"
        local_tz = pytz.timezone("America/Sao_Paulo")
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        local_dt = dt_obj.astimezone(local_tz)
        return local_dt.strftime("%d/%m/%Y %H:%M:%S")

    @app_instance.template_filter("format_for_input")
    def format_for_input_filter(dt_obj):
        if dt_obj is None:
            return ""
        local_tz = pytz.timezone("America/Sao_Paulo")
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        local_dt = dt_obj.astimezone(local_tz)
        return local_dt.strftime("%Y-%m-%dT%H:%M")

    with app_instance.app_context():
        # Registra os Blueprints centralizadamente
        from app.blueprints import register_blueprints
        register_blueprints(app_instance)

        # Registra todos os comandos CLI de uma vez
        from .commands import register_commands
        register_commands(app_instance)

    module_logger.info(
        "Aplicação Flask completamente configurada e pronta para ser retornada."
    )
    return app_instance
