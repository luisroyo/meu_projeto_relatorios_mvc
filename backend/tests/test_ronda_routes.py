# tests/test_ronda_routes.py (VERSÃO FINAL E CORRIGIDA)

from flask import url_for
import os, sys

# Ajuste de path para importar o backend após separação
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models import Ronda, Condominio, User
from datetime import date
import re

def test_registrar_ronda_page_loads(client, test_user):
    """Verifica se a página de registro de ronda carrega para um usuário logado."""
    # Logamos o usuário DENTRO do teste para garantir um estado limpo
    with client:
        client.post(url_for('auth.login'), data={'email': test_user.email, 'password': 'password'})
        response = client.get(url_for('ronda.registrar_ronda'))
        assert response.status_code == 200
        assert b'Registrar Nova Ronda Manual' in response.data

def test_processamento_de_log_na_pagina_registrar(client, test_user, condominio_fixture):
    """Testa se o envio de um log no formulário processa e exibe o relatório na mesma página."""
    with client:
        client.post(url_for('auth.login'), data={'email': test_user.email, 'password': 'password'})
        
        log_exemplo = (
            "[18:36, 06/05/2025] VTR 05: 18:36 início de ronda\n"
            "[18:58, 06/05/2025] VTR 05: 18:57 termino\n"
            "[20:31, 06/05/2025] VTR 05: 20:31 início de ronda\n"
            "[20:58, 06/05/2025] VTR 05: 20:57 termino\n"
            "[23:03, 06/05/2025] VTR 05: 23:03 início de ronda\n"
            "[23:21, 06/05/2025] VTR 05: 23:21 término\n"
            "[01:08, 07/05/2025] VTR 05: 01:08 início de ronda\n"
            "[01:41, 07/05/2025] VTR 05: 01:41 término\n"
            "[04:31, 07/05/2025] VTR 05: 04:30 inicio de ronda\n"
            "[04:47, 07/05/2025] VTR 05: 04:45 termino"
        )
        response = client.post(url_for('ronda.registrar_ronda'), data={
            'nome_condominio': str(condominio_fixture.id),
            'data_plantao': '2025-05-06',
            'escala_plantao': '18h às 06h',
            'log_bruto_rondas': log_exemplo
        })
        html = response.data.decode('utf-8')
        print("\n\n==== CONTEÚDO DA RESPOSTA HTML ====")
        print(html)
        print("==== FIM DO CONTEÚDO ====")
        assert response.status_code == 200
        # Extrair o conteúdo do relatório gerado
        match = re.search(r'<pre id="relatorio-gerado-box" class="[^"]*">([\s\S]*?)</pre', html)
        assert match, "Relatório processado não encontrado no HTML."
        relatorio = match.group(1)
        print("\n==== RELATÓRIO EXTRAÍDO DO HTML ====")
        print(relatorio)
        print("==== FIM DO RELATÓRIO EXTRAÍDO ====")
        assert "Total: 5 rondas completas no plantão" in relatorio
        assert "Início: 18:36  – Término: 18:57" in relatorio
        assert "Início: 20:31  – Término: 20:57" in relatorio
        assert "Início: 23:03  – Término: 23:21" in relatorio
        assert "Início: 01:08  – Término: 01:41" in relatorio
        assert "Início: 04:30  – Término: 04:45" in relatorio

def test_salvar_ronda_via_ajax(client, db, admin_user, condominio_fixture):
    """Testa a rota '/salvar' que cria a ronda no banco."""
    log_exemplo = (
        "[18:36, 06/05/2025] VTR 05: 18:36 início de ronda\n"
        "[18:58, 06/05/2025] VTR 05: 18:57 termino\n"
        "[20:31, 06/05/2025] VTR 05: 20:31 início de ronda\n"
        "[20:58, 06/05/2025] VTR 05: 20:57 termino\n"
        "[23:03, 06/05/2025] VTR 05: 23:03 início de ronda\n"
        "[23:21, 06/05/2025] VTR 05: 23:21 término\n"
        "[01:08, 07/05/2025] VTR 05: 01:08 início de ronda\n"
        "[01:41, 07/05/2025] VTR 05: 01:41 término\n"
        "[04:31, 07/05/2025] VTR 05: 04:30 inicio de ronda\n"
        "[04:47, 07/05/2025] VTR 05: 04:45 termino"
    )
    payload = {
        'ronda_id': None, 'log_bruto': log_exemplo,
        'condominio_id': str(condominio_fixture.id),
        'data_plantao': '2025-05-06', 'escala_plantao': '18h às 06h',
        'supervisor_id': '0'
    }
    assert Ronda.query.count() == 0
    with client:
        client.post('/login', data={'email': 'admin@example.com', 'password': 'adminpass'}, follow_redirects=True)
        response = client.post(url_for('ronda.salvar_ronda'), json=payload)
        print("\nStatus code:", response.status_code)
        print("Location:", getattr(response, 'location', None))
        print("Response data:\n", response.data.decode('utf-8'))
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    assert Ronda.query.count() == 1

def test_excluir_ronda_com_permissao_admin(client, db, admin_user, ronda_existente):
    """Testa se um administrador consegue excluir uma ronda."""
    assert Ronda.query.count() == 1
    with client:
        client.post('/login', data={'email': 'admin@example.com', 'password': 'adminpass'}, follow_redirects=True)
        response = client.post(url_for('ronda.excluir_ronda', ronda_id=ronda_existente.id), follow_redirects=True)
        print("\nStatus code:", response.status_code)
        print("Location:", getattr(response, 'location', None))
        print("Response data:\n", response.data.decode('utf-8'))
    assert response.status_code == 200
    assert f'Ronda #{ronda_existente.id} excluída com sucesso.'.encode('utf-8') in response.data

def test_usuario_comum_nao_pode_excluir_ronda(auth_client, db, ronda_existente):
    """Testa se um usuário comum é bloqueado ao tentar excluir."""
    assert Ronda.query.count() == 1
    
    with auth_client:
        response = auth_client.post(url_for('ronda.excluir_ronda', ronda_id=ronda_existente.id))

    assert response.status_code == 302
    assert Ronda.query.count() == 1

def test_admin_login_persiste(client, db, admin_user):
    """Verifica se o login do admin persiste e permite acesso a rota protegida."""
    with client:
        resp_login = client.post('/login', data={'email': 'admin@example.com', 'password': 'adminpass'}, follow_redirects=True)
        print("\n[LOGIN ADMIN] Status:", resp_login.status_code)
        # Tentar acessar uma rota protegida de admin
        resp_admin = client.get('/admin/ronda_dashboard', follow_redirects=True)
        print("[ADMIN DASHBOARD] Status:", resp_admin.status_code)
        print("[ADMIN DASHBOARD] HTML:\n", resp_admin.data.decode('utf-8'))
        assert resp_admin.status_code == 200
        assert "Dashboard de Métricas de Rondas" in resp_admin.data.decode('utf-8') or "Métricas de Rondas" in resp_admin.data.decode('utf-8')
