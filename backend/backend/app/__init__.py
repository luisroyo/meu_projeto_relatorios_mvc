import logging
import os
import time
from logging.handlers import RotatingFileHandler

import pytz
from flask import Flask, request, jsonify, session, redirect, url_for, flash
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

# Configuração de logs condicional para Vercel (sistema somente leitura)
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
    # No Vercel, apenas usar logging básico sem arquivo
    module_logger.info("Executando no Vercel - usando logging básico sem arquivo")
else:
    # No Render/local, usar arquivo de log
    try:
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
        module_logger.info("Logging para arquivo configurado com sucesso")
    except (OSError, PermissionError) as e:
        module_logger.warning(f"Não foi possível criar arquivo de log: {e}. Usando apenas logging básico.")

# --- Fábrica da aplicação ---
def create_app(config_class=DevelopmentConfig):
    # Diretórios de templates e estáticos ficam fora do pacote backend/app
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    templates_dir = os.path.join(project_root, 'frontend', 'templates')
    static_dir = os.path.join(project_root, 'frontend', 'static')

    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
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
    # Aponta o Flask-Migrate para o diretório correto após a reorganização
    migrate.init_app(app, db, directory=os.path.join(project_root, 'backend', 'migrations'))
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    init_jwt(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    # Servir arquivos estáticos do diretório frontend/static via WhiteNoise
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir)

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

    # Fecha a sessão ao final de cada request para ECONOMIZAR DB
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        try:
            # SEMPRE fecha a sessão para economizar horas de DB
            db.session.remove()
            # Força fechamento da conexão para economizar DB
            if hasattr(db.engine, 'dispose'):
                db.engine.dispose()
        except Exception as e:
            module_logger.error(f"Erro ao encerrar sessão do DB no teardown: {e}")

    # Logout automático por inatividade - OTIMIZADO para economizar DB
    @app.before_request
    def enforce_inactivity_timeout():
        """Força logout por inatividade usando apenas sessão (sem tocar no DB)."""
        try:
            from flask_login import current_user, logout_user
            from datetime import datetime, timezone, timedelta

            # Ignora estáticos, preflight e APIs para economizar DB
            if (request.method == 'OPTIONS' or 
                (request.endpoint and 'static' in request.endpoint) or
                request.path.startswith('/api/')):
                return

            if not current_user.is_authenticated:
                return

            now_utc = datetime.now(timezone.utc)
            max_idle = timedelta(minutes=app.config.get('INACTIVITY_TIMEOUT_MIN', 3))

            # Invalidação global de sessão via cache (se setada por admin)
            try:
                invalidation_ts = cache.get('SESSION_INVALIDATION_TS')
                if invalidation_ts and session.get('login_epoch') and session['login_epoch'] < invalidation_ts:
                    logout_user()
                    flash('Sessão invalidada pelo administrador.', 'warning')
                    return redirect(url_for('auth.login'))
            except Exception:
                pass

            # Lê última atividade da sessão (string ISO) e calcula idle
            last_seen_str = session.get('last_seen_utc')
            if last_seen_str:
                try:
                    # Compatível com valores sem tz (assume UTC)
                    last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    idle = now_utc - last_seen
                    if idle > max_idle:
                        logout_user()
                        flash('Sessão expirada por inatividade.', 'warning')
                        return redirect(url_for('auth.login'))
                except Exception:
                    # Se parsing falhar, apenas redefine abaixo
                    pass

            # Atualiza última atividade na sessão
            session['last_seen_utc'] = now_utc.isoformat()
        except Exception as e:
            module_logger.error(f"Erro no controle de inatividade: {e}")

    # Dev: verificação da conexão (desabilitada para economizar horas de DB)
    # Mantemos a função disponível via flag para debug pontual
    if os.environ.get("DB_CHECK_EACH_REQUEST", "false").lower() == "true":
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

    # Middleware de tracking de atividade - DESABILITADO para economizar DB
    # @app.before_request
    # def track_user_activity():
    #     try:
    #         # Permite desligar rastreamento para evitar hits desnecessários ao DB
    #         if app.config.get('USER_ACTIVITY_ENABLED', False) is True:
    #             from .middleware.user_activity import track_user_activity as track
    #             track()
    #     except Exception as e:
    #         module_logger.error(f"Erro no middleware de atividade: {e}")
    
    # DESABILITADO para economizar horas de banco de dados

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if 'sqlite' in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    module_logger.info("Aplicação Flask configurada e pronta.")
    return app
