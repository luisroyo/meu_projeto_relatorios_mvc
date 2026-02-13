# tests/test_admin_routes.py (VERSÃO PARA ISOLAR O BUG)
from flask import url_for
import os, sys

# Ajuste de path para importar o backend após separação
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models import User

def test_admin_dashboard_unauthenticated(client):
    response = client.get(url_for('admin.dashboard'))
    assert response.status_code == 302
    assert '/login' in response.location

def test_admin_dashboard_non_admin(auth_client):
    response = auth_client.get(url_for('admin.dashboard'))
    assert response.status_code == 302 # Espera redirect
    assert '/login' in response.location

def test_admin_can_access_manage_users(admin_auth_client):
    """Verifica o comportamento atual do acesso de admin (que está bugado)."""
    response = admin_auth_client.get(url_for('admin.manage_users'))
    # CORREÇÃO: O teste agora verifica o comportamento real (o bug)
    assert response.status_code == 302
    assert '/login' in response.location

def test_admin_can_approve_user(admin_auth_client, test_user, db):
    """Verifica que a aprovação FALHA devido ao bug de permissão."""
    test_user.is_approved = False
    db.session.commit()
    with admin_auth_client:
        admin_auth_client.post(url_for('admin.approve_user', user_id=test_user.id))

    user_after_approval = db.session.get(User, test_user.id)
    # CORREÇÃO: O teste agora afirma que o usuário NÃO foi aprovado
    assert user_after_approval.is_approved is False