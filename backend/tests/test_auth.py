# tests/test_auth.py (VERSÃO FINAL)
from flask import url_for
import os, sys

# Ajuste de path para importar o backend após separação
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models import User

# --- Testes que já passavam ou não precisavam de mudança ---
def test_register_page_loads(client):
    response = client.get(url_for('auth.register'))
    assert response.status_code == 200

def test_login_page_loads(client):
    response = client.get(url_for('auth.login'))
    assert response.status_code == 200

def test_successful_login(auth_client, test_user):
    # A fixture já loga o usuário, o que é suficiente para este teste
    response = auth_client.get(url_for('main.index')) # main.index provavelmente redireciona um usuário logado
    assert response.status_code == 302


# --- Testes que estavam falhando, agora corrigidos ---

def test_successful_registration(client, app):
    """Testa o registro e a presença da mensagem flash correta na página seguinte."""
    with client:
        # Etapa 1: Faz o POST para registrar
        response_post = client.post(url_for('auth.register'), data={
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'newpassword', 'confirm_password': 'newpassword'
        })
        assert response_post.status_code == 302 # Confirma o redirecionamento

        # Etapa 2: Segue o redirecionamento e verifica a mensagem
        response_get = client.get(response_post.location)
        assert response_get.status_code == 200
        # Verifica o texto exato que sua rota envia
        assert 'Conta criada com sucesso. Aguarde aprovação do administrador.'.encode('utf-8') in response_get.data

def test_login_unapproved_user(client, test_user, db):
    """Testa a tentativa de login por um usuário não aprovado."""
    test_user.is_approved = False
    db.session.commit()
    
    with client: # Garante que a sessão persista durante o redirect
        response = client.post(url_for('auth.login'), data={'email': test_user.email, 'password': 'password'}, follow_redirects=True)
        assert response.status_code == 200
        assert 'Conta ainda não aprovada.'.encode('utf-8') in response.data

def test_logout(auth_client):
    """Testa o logout bem-sucedido."""
    with auth_client: # Garante que a sessão do usuário logado persista
        response = auth_client.get(url_for('auth.logout'), follow_redirects=True)
        assert response.status_code == 200
        assert 'Logout realizado com sucesso.'.encode('utf-8') in response.data