# app/__init__.py
import os
import logging
from datetime import datetime as dt, timezone # Mantido como dt
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.models import User # Importar User aqui para o bloco de criação
from werkzeug.security import generate_password_hash # Necessário para set_password se User não for importado de .models completo

# Defina as instâncias das extensões AQUI, no nível do módulo
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
# csrf = CSRFProtect() # CSRFProtect não é usado no código abaixo, mas mantenha se o resto do seu app usa.

# Configure o login_manager AQUI
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Configuração básica de logging para o módulo (logger raiz)
# Se você já tem um logger configurado no seu app_instance, pode não precisar deste config global aqui.
# Mas para o module_logger funcionar antes do app_instance.logger estar pronto, é útil.
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

module_logger = logging.getLogger(__name__) # Logger para este módulo __init__

# Carrega variáveis de ambiente do .env na raiz do projeto, se existir
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    module_logger.info(f".env carregado de {dotenv_path}")
else:
    module_logger.info(f".env não encontrado em {dotenv_path}, usando variáveis de ambiente do sistema se definidas.")


def create_app():
    app_instance = Flask(__name__)
    module_logger.info("Instância Flask criada.")

    # Configurações da Aplicação
    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # Corrigido para pegar o diretório raiz do projeto
    default_db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'site.db')
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL_FLASK', default_db_path)
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app_instance.config['WTF_CSRF_ENABLED'] = True # Reabilitar CSRF para segurança

    # Determinar o contexto de execução para controlar logs detalhados
    is_werkzeug_main_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    is_not_flask_debug_mode = str(os.getenv('FLASK_DEBUG', '0')).lower() not in ['1', 'true', 'on']
    should_perform_single_run_actions = is_werkzeug_main_process or is_not_flask_debug_mode

    if should_perform_single_run_actions:
        module_logger.info(f"Banco de dados URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")

    # Inicializa extensões com a app_instance
    db.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("SQLAlchemy inicializado com a app.")
    
    migrate.init_app(app_instance, db)
    if should_perform_single_run_actions: module_logger.info("Flask-Migrate inicializado com a app.")
    
    login_manager.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("Flask-Login inicializado com a app.")
    
    # csrf.init_app(app_instance) # Inicializa CSRF se for usar globalmente
    # Se você importou CSRFProtect no topo, inicialize-o aqui
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app_instance)
    if should_perform_single_run_actions: module_logger.info("CSRFProtect inicializado com a app.")

    # Configuração de Logging da Aplicação Flask (para app_instance.logger)
    if should_perform_single_run_actions:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # Configura o logger da app_instance apenas se não tiver handlers (evita duplicação com reloader)
        if not app_instance.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            app_instance.logger.addHandler(stream_handler)
            app_instance.logger.setLevel(log_level)
            app_instance.logger.propagate = False # Evita que o logger raiz também processe essas mensagens
            module_logger.info(f"Configuração de logging da aplicação Flask (app.logger) aplicada. Nível: {log_level_str}")
        app_instance.logger.info("Logger da aplicação Flask (app.logger) configurado e pronto.")


    with app_instance.app_context():
        from . import models # Importa os modelos aqui, incluindo User
        if should_perform_single_run_actions: module_logger.info("Modelos importados no contexto da app.")

        # --- CÓDIGO TEMPORÁRIO PARA CRIAR USUÁRIO ADMINISTRADOR ---
        # !!! IMPORTANTE: REMOVA ESTE BLOCO DE CÓDIGO APÓS O USUÁRIO SER CRIADO !!!
        admin_email_to_create = "luisroyo25@gmail.com"
        admin_username_to_create = "Luis Royo"
        admin_password_to_create = "edu123cs"

        existing_admin = models.User.query.filter_by(email=admin_email_to_create).first()
        if not existing_admin:
            module_logger.info(f"Usuário administrador {admin_email_to_create} não encontrado, criando...")
            try:
                admin_user = models.User(
                    username=admin_username_to_create,
                    email=admin_email_to_create,
                    is_admin=True,
                    is_approved=True # Ativa o usuário imediatamente
                )
                admin_user.set_password(admin_password_to_create) # A função set_password faz o hash
                db.session.add(admin_user)
                db.session.commit()
                module_logger.info(f"Usuário administrador {admin_email_to_create} criado com sucesso.")
            except Exception as e:
                db.session.rollback()
                module_logger.error(f"Falha ao criar usuário administrador {admin_email_to_create}: {e}", exc_info=True)
        else:
            module_logger.info(f"Usuário administrador {admin_email_to_create} já existe.")
        # --- FIM DO CÓDIGO TEMPORÁRIO ---

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
        app_instance.register_blueprint(ronda_bp, url_prefix='/ronda') # Adicionado prefixo /ronda
        if should_perform_single_run_actions: module_logger.info(f"Blueprint '{ronda_bp.name}' registrado com prefixo '/ronda'.")


    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': dt.now(timezone.utc).year}
    
    if should_perform_single_run_actions:
        module_logger.info("Aplicação Flask completamente configurada e pronta para ser retornada.")
    
    return app_instance