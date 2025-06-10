# tests/test_admin_routes.py
from flask import url_for
from app.models import User

def test_admin_dashboard_unauthenticated(client):
    """Testa se um usuário não logado é redirecionado da área de admin."""
    response = client.get(url_for('admin.dashboard'), follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_admin_dashboard_non_admin(auth_client):
    """Testa se um usuário comum (não admin) é redirecionado da área de admin."""
    response = auth_client.get(url_for('admin.dashboard'), follow_redirects=True)
    assert response.status_code == 200
    assert url_for('main.index') in response.request.path
    assert 'Acesso negado.'.encode('utf-8') in response.data

def test_admin_can_access_manage_users(admin_auth_client, test_user):
    """Testa se um admin consegue acessar a página de gerenciamento de usuários."""
    response = admin_auth_client.get(url_for('admin.manage_users'))
    assert response.status_code == 200
    assert 'Gerenciar Usuários'.encode('utf-8') in response.data
    assert test_user.username.encode('utf-8') in response.data

def test_admin_can_approve_user(admin_auth_client, test_user, db):
    """Testa a funcionalidade de aprovar um usuário."""
    test_user.is_approved = False
    db.session.commit()
    
    admin_auth_client.post(url_for('admin.approve_user', user_id=test_user.id), follow_redirects=True)
    
    # Sintaxe moderna do SQLAlchemy para evitar o warning
    user_after_approval = db.session.get(User, test_user.id)
    assert user_after_approval.is_approved is True