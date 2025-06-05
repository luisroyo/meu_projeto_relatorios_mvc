# tests/conftest.py
import os
import sys

# Adiciona o diretório raiz do projeto (um nível acima de 'tests') ao sys.path
# Isso é CRUCIAL para que 'from app import ...' funcione.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Somente DEPOIS do bloco acima, vêm as outras importações:
import pytest
from app import create_app, db as _db
from app.models import User, Colaborador, Condominio, LoginHistory, Ronda # Adicionado LoginHistory, Ronda
from werkzeug.security import generate_password_hash
from unittest.mock import patch
from flask import url_for
from datetime import date

@pytest.fixture(scope='session')
def app():
    """Cria e configura uma nova instância da aplicação para a sessão de testes."""
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance_path = os.path.join(BASE_DIR, 'instance_test')

    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    test_db_path = 'sqlite:///' + os.path.join(instance_path, 'test_site.db')

    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": test_db_path,
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False,
        "SERVER_NAME": "localhost.localdomain",
        "SECRET_KEY": "test_secret_key",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "REPORT_MAX_CHARS": 1000,
        "DEBUG": False
    })

    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    with flask_app.app_context():
        _db.drop_all()
    
    # import shutil
    # if os.path.exists(instance_path):
    #     shutil.rmtree(instance_path)


@pytest.fixture()
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """Um executor de testes para os comandos Click da aplicação."""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def db(app):
    """Banco de dados de teste para cada função de teste."""
    with app.app_context():
        _db.create_all() 
        yield _db        
        _db.session.remove() 
        _db.drop_all()       

@pytest.fixture
def test_user(db):
    """Cria um usuário de teste."""
    user = User(username='testuser', email='test@example.com', is_approved=True, is_admin=False)
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def admin_user(db):
    """Cria um usuário administrador de teste."""
    admin = User(username='adminuser', email='admin@example.com', is_approved=True, is_admin=True)
    admin.set_password('adminpass')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def auth_client(client, test_user, app): 
    """Um cliente de teste logado como test_user."""
    with app.app_context(): 
        with client:
            client.post(url_for('auth.login'), data={ 
                'email': test_user.email,
                'password': 'password'
            }, follow_redirects=True)
            yield client
            # Logout explícito para limpar a sessão para o próximo teste, se necessário
            client.get(url_for('auth.logout'), follow_redirects=True)


@pytest.fixture
def admin_auth_client(client, admin_user, app): 
    """Um cliente de teste logado como admin_user."""
    with app.app_context():
        with client:
            client.post(url_for('auth.login'), data={ 
                'email': admin_user.email,
                'password': 'adminpass'
            }, follow_redirects=True)
            yield client
            # Logout explícito
            client.get(url_for('auth.logout'), follow_redirects=True)


@pytest.fixture
def test_colaborador(db):
    """Cria um colaborador de teste."""
    colaborador = Colaborador(
        nome_completo="João Testador Silva",
        matricula="12345",
        cargo="Vigilante de Testes",
        status="Ativo",
        data_admissao=date(2022, 1, 1) 
    )
    db.session.add(colaborador)
    db.session.commit()
    return colaborador

# --- Mocks de Serviços ---
@pytest.fixture
def mock_base_generative_service():
    with patch('app.services.base_generative_service.BaseGenerativeService._call_generative_model') as mock_call:
        yield mock_call
        
@pytest.fixture
def mock_patrimonial_service():
    with patch('app.services.patrimonial_report_service.PatrimonialReportService.gerar_relatorio_seguranca') as mock_method:
        yield mock_method

@pytest.fixture
def mock_email_service():
    with patch('app.services.email_format_service.EmailFormatService.formatar_para_email') as mock_method:
        yield mock_method

@pytest.fixture
def mock_justificativa_atestado_service():
    with patch('app.services.justificativa_service.JustificativaAtestadoService.gerar_justificativa') as mock_method:
        yield mock_method

@pytest.fixture
def mock_justificativa_troca_plantao_service():
    with patch('app.services.justificativa_troca_plantao_service.JustificativaTrocaPlantaoService.gerar_justificativa_troca') as mock_method:
        yield mock_method
        
@pytest.fixture
def mock_ronda_processor():
    with patch('app.services.ronda_logic.processor.processar_log_de_rondas') as mock_process:
        yield mock_process