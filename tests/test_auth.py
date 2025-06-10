# tests/test_auth.py
from flask import url_for
from app.models import User

def test_register_page_loads(client):
    """Testa se a página de registro carrega corretamente."""
    response = client.get(url_for('auth.register'))
    assert response.status_code == 200
    assert "Criar Nova Conta".encode('utf-8') in response.data

def test_successful_registration(client, app):
    """Testa o registro bem-sucedido de um usuário."""
    response = client.post(url_for('auth.register'), data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Conta criada com sucesso.'.encode('utf-8') in response.data
    
    with app.app_context():
        user = User.query.filter_by(email='new@example.com').first()
        assert user is not None
        assert user.username == 'newuser'
        assert not user.is_approved

def test_login_page_loads(client):
    """Testa se a página de login carrega."""
    response = client.get(url_for('auth.login'))
    assert response.status_code == 200
    assert "Acessar Conta".encode('utf-8') in response.data

def test_successful_login(client, test_user):
    """Testa o login bem-sucedido de um usuário aprovado."""
    response = client.post(url_for('auth.login'), data={
        'email': test_user.email,
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert f'Bem-vindo, {test_user.username}!'.encode('utf-8') in response.data

def test_login_unapproved_user(client, test_user, db):
    """Testa a tentativa de login por um usuário não aprovado."""
    test_user.is_approved = False
    db.session.commit()

    response = client.post(url_for('auth.login'), data={
        'email': test_user.email,
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Conta ainda não aprovada.'.encode('utf-8') in response.data

def test_logout(auth_client):
    """Testa o logout bem-sucedido."""
    response = auth_client.get(url_for('auth.logout'), follow_redirects=True)
    assert response.status_code == 200
    assert 'Logout realizado com sucesso.'.encode('utf-8') in response.data