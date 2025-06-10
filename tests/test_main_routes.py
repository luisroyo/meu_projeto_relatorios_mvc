# tests/test_main_routes.py

import pytest
from unittest.mock import patch, MagicMock
from flask import url_for

def test_index_page_requires_login(client):
    """Testa se a página inicial redireciona para o login se o usuário não estiver logado."""
    response = client.get(url_for('main.index'))
    assert response.status_code == 302
    assert '/login' in response.location

def test_index_page_loads_for_logged_in_user(auth_client):
    """Testa se a página inicial carrega para um usuário logado."""
    response = auth_client.get(url_for('main.index'))
    assert response.status_code == 200
    assert 'Analisador de Relatórios IA'.encode('utf-8') in response.data

@patch('app.blueprints.main.routes._get_email_service')
@patch('app.blueprints.main.routes._get_patrimonial_service')
def test_processar_relatorio_success(mock_get_patrimonial, mock_get_email, auth_client):
    """Testa o endpoint /processar_relatorio com sucesso."""
    mock_patrimonial_service = MagicMock()
    mock_patrimonial_service.gerar_relatorio_seguranca.return_value = "Relatório patrimonial gerado."
    mock_get_patrimonial.return_value = mock_patrimonial_service

    mock_email_service = MagicMock()
    mock_email_service.formatar_para_email.return_value = "Relatório formatado para e-mail."
    mock_get_email.return_value = mock_email_service

    payload = {
        'relatorio_bruto': 'Conteúdo do relatório.',
        'format_for_email': True
    }
    response = auth_client.post(url_for('main.processar_relatorio'), json=payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['relatorio_processado'] == "Relatório patrimonial gerado."
    assert json_data['relatorio_email'] == "Relatório formatado para e-mail."

def test_processar_relatorio_invalid_payload(auth_client):
    """Testa o endpoint com payload inválido."""
    response = auth_client.post(url_for('main.processar_relatorio'), json={'relatorio_bruto': ''})
    assert response.status_code == 400
    assert 'obrigatório' in response.get_json()['erro']

def test_processar_relatorio_not_json(auth_client):
    """Testa se o endpoint rejeita requisições que não são JSON."""
    response = auth_client.post(url_for('main.processar_relatorio'), data={'relatorio_bruto': 'dado'})
    assert response.status_code == 400
    assert 'Formato inválido' in response.get_json()['erro']