# tests/conftest.py
import os
import sys
import pytest
from unittest.mock import patch

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa os componentes da aplicação APÓS configurar o path
from app import create_app, db as _db
from app.models import User, Colaborador

@pytest.fixture(scope='session')
def app():
    """Cria a instância da aplicação uma única vez para toda a sessão de testes."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Usa DB em memória, mais rápido
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-for-session",
        "SERVER_NAME": "localhost.local",
    })
    return app

@pytest.fixture(scope='function')
def db(app):
    """
    Uma fixture que garante um banco de dados limpo para cada teste.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Um executor de CLI para a aplicação."""
    return app.test_cli_runner()

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

@pytest.fixture
def auth_client(client, test_user):
    """Retorna um cliente de teste já logado como um usuário padrão."""
    with client:
        client.post('/login', data={'email': test_user.email, 'password': 'password'}, follow_redirects=True)
        yield client

@pytest.fixture
def admin_auth_client(client, admin_user):
    """Retorna um cliente de teste já logado como um usuário administrador."""
    with client:
        client.post('/login', data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
        yield client