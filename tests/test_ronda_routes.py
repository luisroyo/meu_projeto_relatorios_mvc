# tests/test_ronda_routes.py (VERSÃO FINAL E CORRIGIDA)

from flask import url_for
from app.models import Ronda, Condominio, User
from datetime import date

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
        
        log_exemplo = "[08:00, 10/07/2025] VTR 01: Início ronda\n[08:12, 10/07/2025] VTR 01: Término ronda"
        
        response = client.post(url_for('ronda.registrar_ronda'), data={
            'nome_condominio': str(condominio_fixture.id),
            'data_plantao': '2025-07-10',
            'escala_plantao': '06h às 18h',
            'log_bruto_rondas': log_exemplo
        })
        
        assert response.status_code == 200
        # CORREÇÃO: O texto do assert agora corresponde exatamente ao que report.py gera.
        assert b'Total: 1 rondas completas no plant' in response.data
        assert b'In\xc3\xadcio: 08:00' in response.data # Início
        assert b'T\xc3\xa9rmino: 08:12' in response.data # Término

def test_salvar_ronda_via_ajax(admin_auth_client, db, condominio_fixture):
    """Testa a rota '/salvar' que cria a ronda no banco."""
    log_exemplo = "[10:00, 11/07/2025] VTR 02: Início\n[10:20, 11/07/2025] VTR 02: Fim"
    
    payload = {
        'ronda_id': None, 'log_bruto': log_exemplo,
        'condominio_id': str(condominio_fixture.id),
        'data_plantao': '2025-07-11', 'escala_plantao': '06h às 18h',
        'supervisor_id': '0'
    }

    assert Ronda.query.count() == 0
    # CORREÇÃO: Usando 'with' para garantir que a sessão de admin persista.
    with admin_auth_client:
        response = admin_auth_client.post(url_for('ronda.salvar_ronda'), json=payload)

    assert response.status_code == 200
    assert response.get_json()['success'] is True
    assert Ronda.query.count() == 1

def test_excluir_ronda_com_permissao_admin(admin_auth_client, db, ronda_existente):
    """Testa se um administrador consegue excluir uma ronda."""
    assert Ronda.query.count() == 1
    
    # CORREÇÃO: Usando 'with' para garantir que a sessão de admin persista.
    with admin_auth_client:
        response = admin_auth_client.post(url_for('ronda.excluir_ronda', ronda_id=ronda_existente.id), follow_redirects=True)
    
    assert response.status_code == 200
    assert f'Ronda #{ronda_existente.id} excluída com sucesso.'.encode('utf-8') in response.data
    assert Ronda.query.count() == 0

def test_usuario_comum_nao_pode_excluir_ronda(auth_client, db, ronda_existente):
    """Testa se um usuário comum é bloqueado ao tentar excluir."""
    assert Ronda.query.count() == 1
    
    with auth_client:
        response = auth_client.post(url_for('ronda.excluir_ronda', ronda_id=ronda_existente.id))

    assert response.status_code == 302
    assert Ronda.query.count() == 1
