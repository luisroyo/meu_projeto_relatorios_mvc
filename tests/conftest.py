# tests/conftest.py
import sys
import os

import pytest

# Adiciona o diretório raiz do projeto ao sys.path
# Isso garante que o Python possa encontrar o pacote 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Agora as importações do seu projeto devem funcionar
from app import create_app, db as _db 
from app.models import User, Colaborador, Condominio
from werkzeug.security import generate_password_hash
from unittest.mock import patch



@pytest.fixture(scope='session')
def app():
    """Cria e configura uma nova instância da aplicação para a sessão de testes."""
    import os
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance_path = os.path.join(BASE_DIR, 'instance_test') # Caminho da instância separado para testes

    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    test_db_path = 'sqlite:///' + os.path.join(instance_path, 'test_site.db')

    flask_app = create_app() #
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": test_db_path,
        "WTF_CSRF_ENABLED": False,  # Desabilita CSRF para simplificar testes de formulários
        "LOGIN_DISABLED": False,     # Garante que o login está habilitado para testes de autenticação
        "SERVER_NAME": "localhost.localdomain", # Para url_for funcionar sem uma requisição ativa
        "SECRET_KEY": "test_secret_key", # Chave secreta específica para testes
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "REPORT_MAX_CHARS": 1000, # Limite menor para testes, se aplicável
        "DEBUG": False # Desabilitar modo debug nos testes para evitar logs excessivos ou comportamento inesperado do reloader
    })

    with flask_app.app_context():
        _db.create_all() # Cria todas as tabelas

    yield flask_app

    # Limpeza após os testes
    with flask_app.app_context():
        _db.drop_all()
    
    # Opcional: remover a pasta de instância de teste
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

@pytest.fixture(scope='function') # Usar escopo de função para o db para garantir isolamento
def db(app):
    """Banco de dados de teste para toda a sessão."""
    with app.app_context():
        _db.create_all() # Garante que as tabelas foram criadas
        yield _db
        _db.session.remove() # Limpa a sessão
        _db.drop_all()       # Remove todas as tabelas para garantir um estado limpo para o próximo teste

@pytest.fixture
def test_user(db):
    """Cria um usuário de teste."""
    user = User(username='testuser', email='test@example.com', is_approved=True, is_admin=False) #
    user.set_password('password') #
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def admin_user(db):
    """Cria um usuário administrador de teste."""
    admin = User(username='adminuser', email='admin@example.com', is_approved=True, is_admin=True) #
    admin.set_password('adminpass') #
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def auth_client(client, test_user):
    """Um cliente de teste logado como test_user."""
    with client:
        client.post('/login', data={ #
            'email': test_user.email,
            'password': 'password'
        }, follow_redirects=True)
        yield client
        client.get('/logout', follow_redirects=True) # Garante o logout após o teste

@pytest.fixture
def admin_auth_client(client, admin_user):
    """Um cliente de teste logado como admin_user."""
    with client:
        client.post('/login', data={ #
            'email': admin_user.email,
            'password': 'adminpass'
        }, follow_redirects=True)
        yield client
        client.get('/logout', follow_redirects=True) #

@pytest.fixture
def mock_base_generative_service():
    """Simula o método _call_generative_model da BaseGenerativeService."""
    with patch('app.services.base_generative_service.BaseGenerativeService._call_generative_model') as mock_call: #
        yield mock_call
        
@pytest.fixture
def mock_patrimonial_service():
    with patch('app.services.patrimonial_report_service.PatrimonialReportService.gerar_relatorio_seguranca') as mock_method: #
        yield mock_method

@pytest.fixture
def mock_email_service():
    with patch('app.services.email_format_service.EmailFormatService.formatar_para_email') as mock_method: #
        yield mock_method

@pytest.fixture
def mock_justificativa_atestado_service():
    with patch('app.services.justificativa_service.JustificativaAtestadoService.gerar_justificativa') as mock_method: #
        yield mock_method

@pytest.fixture
def mock_justificativa_troca_plantao_service():
    with patch('app.services.justificativa_troca_plantao_service.JustificativaTrocaPlantaoService.gerar_justificativa_troca') as mock_method: #
        yield mock_method
        
@pytest.fixture
def mock_ronda_processor():
    """Simula a função processar_log_de_rondas."""
    # Assumindo que processar_log_de_rondas é importado em app.blueprints.ronda.routes
    # Ajuste o caminho se for importado em outro lugar ou usado diretamente por um método de classe de serviço
    with patch('app.services.ronda_logic.processor.processar_log_de_rondas') as mock_process: #
        yield mock_process