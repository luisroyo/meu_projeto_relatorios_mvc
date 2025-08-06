import logging
import os
import time
from logging.handlers import RotatingFileHandler

import pytz
from flask import Flask, request, jsonify
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from whitenoise import WhiteNoise
from flask_cors import CORS
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError, DisconnectionError

from app.auth.jwt_auth import init_jwt
from config import DevelopmentConfig

# Carrega .env se disponível
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Instância das extensões ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()

redis_url = os.environ.get("REDIS_URL", "memory://")

if os.environ.get("FLASK_ENV", "development") == "development":
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["10000 per hour"],
        storage_uri=redis_url
    )
else:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per hour", "10000 per day"],
        storage_uri=redis_url
    )

# --- Logging ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
module_logger = logging.getLogger(__name__)

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "assistente_ia_seg.log")

file_handler = RotatingFileHandler(
    log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s"
))
file_handler.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logging.getLogger().addHandler(file_handler)

# --- Fábrica da aplicação ---
def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Desabilitar redirecionamento automático para evitar problemas CORS
    app.url_map.strict_slashes = False

    # CORS
    allowed_origins = [
        "http://localhost:5173", "http://localhost:5174",
        "http://localhost:8081", "http://localhost:3000",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174",
        "http://[::1]:5173", "http://[::1]:5174",
        "https://processador-relatorios-ia.onrender.com",
        "https://ocorrencias-master-app.onrender.com"
    ]
    # CORS básico
    CORS(
        app,
        origins=allowed_origins,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        supports_credentials=True
    )
    
    # ATUALIZAÇÃO DO CORS: Lidando corretamente com preflight
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        return response

    # Inicialização de extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    init_jwt(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    app.wsgi_app = WhiteNoise(app.wsgi_app, root="app/static/")

    # Filtros de template
    @app.template_filter("localtime")
    def localtime_filter(dt_obj):
        if dt_obj is None:
            return "N/A"
        local_tz = pytz.timezone("America/Sao_Paulo")
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        return dt_obj.astimezone(local_tz).strftime("%d/%m/%Y %H:%M:%S")

    @app.template_filter("format_for_input")
    def format_for_input_filter(dt_obj):
        if dt_obj is None:
            return ""
        local_tz = pytz.timezone("America/Sao_Paulo")
        if dt_obj.tzinfo is None:
            dt_obj = pytz.utc.localize(dt_obj)
        return dt_obj.astimezone(local_tz).strftime("%Y-%m-%dT%H:%M")

    with app.app_context():
        from app.blueprints import register_blueprints
        register_blueprints(app)

        # CSRF
        api_blueprints = [
            'api', 'auth_api', 'dashboard_api', 'ocorrencia_api',
            'ronda_api', 'admin_api', 'analisador_api', 'config_api'
        ]
        for blueprint_name in api_blueprints:
            bp = app.blueprints.get(blueprint_name)
            if bp:
                csrf.exempt(bp)

        # CSRF já está desabilitado para os blueprints da API acima
        # Não precisamos do before_request para isso

        # Handler específico para OPTIONS que evita redirecionamentos
        @app.route('/api/ocorrencias', methods=['OPTIONS'])
        @app.route('/api/ocorrencias/', methods=['OPTIONS'])
        @app.route('/api/rondas', methods=['OPTIONS'])
        @app.route('/api/rondas/', methods=['OPTIONS'])
        def handle_specific_options():
            response = jsonify({'message': 'OK'})
            response.status_code = 200
            return response
        
        # Handler genérico para outras rotas da API
        @app.route('/api/<path:path>', methods=['OPTIONS'])
        def handle_api_options(path):
            response = jsonify({'message': 'OK'})
            response.status_code = 200
            return response

        # CLI
        from .commands import register_commands
        register_commands(app)

    # Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            module_logger.error(f"Erro ao carregar usuário {user_id}: {e}")
            return None

    # Tratamento de erros
    @app.errorhandler(OperationalError)
    def handle_operational_error(error):
        if "SSL connection has been closed" in str(error):
            module_logger.warning("Conexão SSL fechada, tentando reconectar...")
            time.sleep(1)
            try:
                db.session.rollback()
                db.session.close()
                db.engine.dispose()
                return jsonify({
                    'error': 'Serviço temporariamente indisponível. Tente novamente.',
                    'code': 'DB_CONNECTION_ERROR'
                }), 503
            except Exception as e:
                module_logger.error(f"Erro ao tentar reconectar: {e}")
                return jsonify({
                    'error': 'Erro interno do servidor',
                    'code': 'DB_RECONNECTION_FAILED'
                }), 500
        else:
            module_logger.error(f"Erro operacional: {error}")
            return jsonify({
                'error': 'Erro interno do servidor',
                'code': 'DB_OPERATIONAL_ERROR'
            }), 500

    @app.errorhandler(DisconnectionError)
    def handle_disconnection_error(error):
        module_logger.error(f"Erro de desconexão: {error}")
        try:
            db.session.rollback()
            db.session.close()
        except:
            pass
        return jsonify({
            'error': 'Conexão com o banco perdida. Tente novamente.',
            'code': 'DB_DISCONNECTION'
        }), 503

    # Dev: verificação da conexão
    if os.environ.get("FLASK_ENV", "development") == "development":
        @app.before_request
        def check_db_connection():
            if request.endpoint and 'static' not in request.endpoint:
                try:
                    db.session.execute(text('SELECT 1'))
                except (OperationalError, DisconnectionError) as e:
                    module_logger.warning(f"Conexão perdida: {e}")
                    try:
                        db.session.rollback()
                        db.session.close()
                        db.engine.dispose()
                    except:
                        pass

    # Middleware de tracking de atividade - aplicado em todos os ambientes
    @app.before_request
    def track_user_activity():
        try:
            from .middleware.user_activity import track_user_activity as track
            track()
        except Exception as e:
            module_logger.error(f"Erro no middleware de atividade: {e}")

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if 'sqlite' in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        @event.listens_for(db.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            module_logger.debug("Conexão obtida do pool")

        @event.listens_for(db.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            module_logger.debug("Conexão devolvida ao pool")

    module_logger.info("Aplicação Flask configurada e pronta.")
    return app
