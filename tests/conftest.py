# tests/conftest.py (VERSÃO FINAL CORRIGIDA)
from datetime import date
import os
import sys
import pytest

# Garante que o Python encontre os módulos dentro de backend/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app, db as _db
from app.models import Condominio, Ronda, User
from config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Cria uma instância da aplicação com configuração de teste para toda a sessão."""
    app = create_app(config_class=TestingConfig)
    return app

# Esta é a mudança chave. Usamos o contexto do app para todas as operações.
@pytest.fixture(scope='function')
def db(app):
    """Configura e limpa o banco de dados para cada teste."""
    with app.app_context():
        _db.create_all()
        yield _db
        # Garante que a sessão seja fechada e o banco de dados limpo
        _db.session.close()
        _db.drop_all()

@pytest.fixture(scope='function')
def client(app, db): # Adicionamos a dependência 'db' para garantir a ordem
    """Um cliente de teste para a aplicação."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Um executor de CLI para a aplicação."""
    return app.test_cli_runner()

# Fixtures de usuário
@pytest.fixture
def test_user(db):
    """Cria um usuário padrão para testes."""
    user = User(username='testuser', email='test@example.com', is_approved=True)
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def admin_user(db):
    """Cria um usuário administrador para testes."""
    admin = User(username='adminuser', email='admin@example.com', is_approved=True, is_admin=True)
    admin.set_password('adminpass')
    db.session.add(admin)
    db.session.commit()
    return admin

# Fixtures de cliente autenticado
@pytest.fixture
def auth_client(client, test_user):
    """Retorna um cliente de teste já logado como um usuário padrão."""
    # O 'client' já está no contexto do app por causa da dependência 'db'
    client.post('/auth/login', data={'email': test_user.email, 'password': 'password'}, follow_redirects=True)
    yield client

@pytest.fixture
def admin_auth_client(client, admin_user):
    """Retorna um cliente de teste já logado como um usuário administrador."""
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
    yield client

@pytest.fixture
def condominio_fixture(db):
    """Cria um condomínio padrão para ser usado nos testes."""
    condo = Condominio(nome="Residencial Teste Fixture")
    db.session.add(condo)
    db.session.commit()
    return condo

@pytest.fixture
def ronda_existente(db, test_user, condominio_fixture):
    """Cria uma ronda padrão no banco de dados para testes de edição/exclusão."""
    ronda = Ronda(
        log_ronda_bruto="[10:00, 01/07/2025] VTR 01: Início ronda\n[10:15, 01/07/2025] VTR 01: Término ronda",
        relatorio_processado="Plantão 01/07/2025...\nTotal: 1 rondas...",
        data_plantao_ronda=date(2025, 7, 1),
        escala_plantao="06h às 18h",
        turno_ronda="Diurno Impar",
        total_rondas_no_log=1,
        duracao_total_rondas_minutos=15,
        user_id=test_user.id,
        condominio_id=condominio_fixture.id
    )
    db.session.add(ronda)
    db.session.commit()
    return ronda
