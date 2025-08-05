# app/__init__.py (VERSÃO CORRIGIDA COM AUTOMAÇÃO DE RONDAS)

import logging
import os
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
from app.auth.jwt_auth import init_jwt
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError, DisconnectionError
import time



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

# Limites diferentes para desenvolvimento e produção
if os.environ.get("FLASK_ENV", "development") == "development":
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["10000 per hour"],
        storage_uri=redis_url
    )
else:
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

    # Habilita CORS para todas as rotas da API
    CORS(
        app_instance,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173", "http://localhost:5174", "http://localhost:8081", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://[::1]:5173", "http://[::1]:5174", "https://processador-relatorios-ia.onrender.com"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
                "expose_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
                "supports_credentials": True,
                "max_age": 86400
            }
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        expose_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:8081", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://[::1]:5173", "http://[::1]:5174"]
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
    
    # Inicializa JWT
    init_jwt(app_instance)

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

        # Desabilita CSRF para todas as rotas da API
        api_blueprints = ['api', 'auth_api', 'dashboard_api', 'ocorrencia_api', 'ronda_api', 'admin_api']
        for blueprint_name in api_blueprints:
            api_blueprint = app_instance.blueprints.get(blueprint_name)
            if api_blueprint:
                csrf.exempt(api_blueprint)

        # Adiciona handler para OPTIONS requests (preflight CORS)
        @app_instance.route('/api/<path:path>', methods=['OPTIONS'])
        def handle_options(path):
            response = app_instance.make_response('')
            # Permitir múltiplas origens
            origin = request.headers.get('Origin')
            allowed_origins = [
                'http://localhost:5173',
                'http://localhost:5174', 
                'http://localhost:8081',
                'http://localhost:3000',
                'http://127.0.0.1:5173',
                'http://127.0.0.1:5174',
                'http://[::1]:5173',
                'http://[::1]:5174'
            ]
            
            if origin in allowed_origins:
                response.headers.add('Access-Control-Allow-Origin', origin)
            else:
                response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
                
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '86400')
            return response

        # Registra todos os comandos CLI de uma vez
        from .commands import register_commands
        register_commands(app_instance)

    # Configurar tratamento de erros de conexão SSL
    @app_instance.errorhandler(OperationalError)
    def handle_operational_error(error):
        """Trata erros de conexão com o banco de dados."""
        if "SSL connection has been closed" in str(error):
            module_logger.warning("Conexão SSL fechada, tentando reconectar...")
            
            # Aguarda um pouco antes de tentar novamente
            time.sleep(1)
            
            try:
                # Tenta reconectar
                db.session.rollback()
                db.session.close()
                db.engine.dispose()
                
                # Retorna erro 503 para indicar serviço temporariamente indisponível
                return jsonify({
                    'error': 'Serviço temporariamente indisponível. Tente novamente em alguns segundos.',
                    'code': 'DB_CONNECTION_ERROR'
                }), 503
                
            except Exception as e:
                module_logger.error(f"Erro ao tentar reconectar: {e}")
                return jsonify({
                    'error': 'Erro interno do servidor',
                    'code': 'DB_RECONNECTION_FAILED'
                }), 500
        else:
            # Para outros erros operacionais, log e retorna erro genérico
            module_logger.error(f"Erro operacional do banco: {error}")
            return jsonify({
                'error': 'Erro interno do servidor',
                'code': 'DB_OPERATIONAL_ERROR'
            }), 500
    
    @app_instance.errorhandler(DisconnectionError)
    def handle_disconnection_error(error):
        """Trata erros de desconexão."""
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
    
    # Middleware para verificar conexão antes de cada request
    @app_instance.before_request
    def check_db_connection():
        """Verifica se a conexão com o banco está ativa antes de cada request."""
        if request.endpoint and 'static' not in request.endpoint:
            try:
                # Testa a conexão com uma query simples
                db.session.execute(text('SELECT 1'))
            except (OperationalError, DisconnectionError) as e:
                module_logger.warning(f"Conexão com banco perdida, tentando reconectar: {e}")
                
                try:
                    db.session.rollback()
                    db.session.close()
                    db.engine.dispose()
                except:
                    pass
    
    # Configurar eventos do SQLAlchemy para logging (dentro do contexto da aplicação)
    with app_instance.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configurações específicas para SQLite (se usado)."""
            if 'sqlite' in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        @event.listens_for(db.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log quando uma conexão é obtida do pool."""
            module_logger.debug("Conexão obtida do pool")
        
        @event.listens_for(db.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log quando uma conexão é devolvida ao pool."""
            module_logger.debug("Conexão devolvida ao pool")

    module_logger.info(
        "Aplicação Flask completamente configurada e pronta para ser retornada."
    )
    return app_instance

