import os
import logging
import datetime
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # ATUALIZADO para refletir o blueprint
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

module_logger = logging.getLogger(__name__) # Logger para este módulo __init__

def create_app():
    app_instance = Flask(__name__)
    module_logger.info("Instância Flask criada.")

    app_instance.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'site.db'))
    app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    module_logger.info(f"Banco de dados URI: {app_instance.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app_instance)
    module_logger.info("SQLAlchemy inicializado com a app.")
    migrate.init_app(app_instance, db)
    module_logger.info("Flask-Migrate inicializado com a app.")
    login_manager.init_app(app_instance)
    module_logger.info("Flask-Login inicializado com a app.")
    
    # Configuração de Logging (movida para ser feita apenas uma vez)
    if not app_instance.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Evita configurar logging duas vezes com o reloader do Werkzeug
        # Ou pode-se fazer a configuração de logging fora da factory se preferir
        # Mas é importante que o logger da app_instance seja configurado.
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True # Para sobrescrever qualquer config anterior do root logger se houver
        )
        # Se você quer que o logger do Flask (app_instance.logger) use essa config:
        app_instance.logger.setLevel(logging.INFO)
        # Se basicConfig já configura o root, e o logger do flask é filho, ele herda.
        # Garantir que não haja handlers duplicados:
        # app_instance.logger.handlers.clear() # Cuidado com isso
        # for handler in logging.getLogger().handlers:
        #    app_instance.logger.addHandler(handler)
        module_logger.info("Configuração de logging básica aplicada/revisada.")


    with app_instance.app_context():
        from . import models 
        module_logger.info("Modelos importados no contexto da app.")

        # --- REGISTRO DO BLUEPRINT ---
        from .routes import main_bp # Importa o blueprint de routes.py
        app_instance.register_blueprint(main_bp)
        module_logger.info("Blueprint 'main_bp' registrado.")
        # Se você tiver outros blueprints, registre-os aqui também.


    @app_instance.context_processor
    def inject_current_year():
        return {'SCRIPT_CURRENT_YEAR': datetime.datetime.now(datetime.timezone.utc).year}
    
    module_logger.info("Aplicação Flask completamente configurada e pronta.")
    return app_instance