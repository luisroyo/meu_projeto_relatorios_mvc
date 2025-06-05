# tests/test_admin_routes.py
from flask import url_for, get_flashed_messages # Adicionado get_flashed_messages
from app.models import User
from app import db

# ... (outros testes que já estavam passando omitidos para brevidade) ...

def test_revoke_self_approval_fails_flash(client, admin_user, db):
    with client: # Garante que estamos no contexto da aplicação
        # Login manual para controlar a sessão
        client.post(url_for('auth.login'), data={
            'email': admin_user.email,
            'password': 'adminpass'
        }, follow_redirects=True)

        response_post = client.post(url_for('admin.revoke_user', user_id=admin_user.id)) # Sem follow_redirects
        assert response_post.status_code == 302 # Espera redirect para manage_users

        # Verifica as mensagens flash na sessão
        flashed_messages = get_flashed_messages(with_categories=True)
        assert len(flashed_messages) >= 1 # Pode haver outras mensagens de login bem-sucedido
        
        found_message = False
        for category, message in flashed_messages:
            if category == 'danger' and "Você não pode revogar sua própria aprovação." in message:
                found_message = True
                break
        assert found_message, "Mensagem flash esperada não encontrada"

        # Verifica se o estado do usuário não mudou
        current_admin_user = db.session.get(User, admin_user.id)
        assert current_admin_user.is_approved

def test_toggle_self_admin_status_fails_flash(client, admin_user, db):
    with client:
        client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
        response_post = client.post(url_for('admin.toggle_admin', user_id=admin_user.id))
        assert response_post.status_code == 302
        
        flashed_messages = get_flashed_messages(with_categories=True)
        assert len(flashed_messages) >= 1
        found_message = False
        for category, message in flashed_messages:
            if category == 'warning' and "Você não pode alterar seu próprio status de administrador." in message:
                found_message = True
                break
        assert found_message, "Mensagem flash esperada não encontrada"

        current_admin_user = db.session.get(User, admin_user.id)
        assert current_admin_user.is_admin

def test_delete_self_fails_flash(client, admin_user, db):
    with client:
        client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
        response_post = client.post(url_for('admin.delete_user', user_id=admin_user.id))
        assert response_post.status_code == 302
        
        flashed_messages = get_flashed_messages(with_categories=True)
        assert len(flashed_messages) >= 1
        found_message = False
        for category, message in flashed_messages:
            if category == 'danger' and "Você não pode deletar sua própria conta." in message:
                found_message = True
                break
        assert found_message, "Mensagem flash esperada não encontrada"
        
        current_admin_user = db.session.get(User, admin_user.id)
        assert current_admin_user is not None

# --- Teste da API para Justificativas ---
def test_api_processar_justificativa_invalid_payload(admin_auth_client):
    response = admin_auth_client.post(url_for('admin.api_processar_justificativa'), json={})
    assert response.status_code == 400
    data = response.get_json()
    # Corrigido para usar strings Unicode diretamente
    assert "Dados não fornecidos." in data['erro'] or "Dados inválidos" in data['erro'] # Ajuste conforme a msg exata da sua rota