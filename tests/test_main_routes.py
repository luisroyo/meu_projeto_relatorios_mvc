# tests/test_main_routes.py
from flask import url_for
import json

def test_index_page_unauthenticated(client):
    """Testa index page redirects to login if not authenticated."""
    response = client.get(url_for('main.index'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('auth.login') in response.location

def test_index_page_authenticated(auth_client):
    """Testa index page loads if authenticated."""
    response = auth_client.get(url_for('main.index'))
    assert response.status_code == 200
    assert b"Analisador de Relat" in response.data # "Analisador de Relatórios IA"

def test_processar_relatorio_api_success(auth_client, mock_patrimonial_service, mock_email_service):
    """Testa successful /processar_relatorio API call."""
    mock_patrimonial_service.return_value = "Relatório Padrão Processado"
    mock_email_service.return_value = "Relatório Email Formatado"

    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': 'Texto bruto aqui', 'format_for_email': True})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['relatorio_processado'] == "Relatório Padrão Processado"
    assert data['relatorio_email'] == "Relatório Email Formatado"
    assert data['erro'] is None
    assert data['erro_email'] is None
    mock_patrimonial_service.assert_called_once_with('Texto bruto aqui')
    mock_email_service.assert_called_once_with("Relatório Padrão Processado")


def test_processar_relatorio_api_no_email(auth_client, mock_patrimonial_service, mock_email_service):
    """Testa /processar_relatorio API call without email formatting."""
    mock_patrimonial_service.return_value = "Relatório Padrão Processado"

    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': 'Outro texto bruto', 'format_for_email': False})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['relatorio_processado'] == "Relatório Padrão Processado"
    assert data['relatorio_email'] is None
    assert data['erro'] is None
    assert data['erro_email'] is None
    mock_patrimonial_service.assert_called_once_with('Outro texto bruto')
    mock_email_service.assert_not_called()

def test_processar_relatorio_api_empty_input(auth_client):
    """Testa /processar_relatorio API com entrada vazia."""
    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': '', 'format_for_email': False})
    assert response.status_code == 400
    data = response.get_json()
    assert "relatorio_bruto é obrigatório" in data['erro'] #

def test_processar_relatorio_api_too_long(auth_client, app):
    """Testa /processar_relatorio API com relatório muito longo."""
    max_chars = app.config.get('REPORT_MAX_CHARS', 12000) 
    long_text = 'a' * (max_chars + 1)
    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': long_text, 'format_for_email': False})
    assert response.status_code == 413 # Payload Too Large
    data = response.get_json()
    assert f"Relatório muito longo (máximo de {max_chars}" in data['erro'] #

def test_processar_relatorio_api_patrimonial_service_error(auth_client, mock_patrimonial_service):
    """Testa API quando o serviço patrimonial levanta uma exceção."""
    mock_patrimonial_service.side_effect = Exception("Falha no serviço IA Patrimonial")
    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': 'Texto qualquer', 'format_for_email': False})
    assert response.status_code == 500 # Ajustado conforme a lógica da rota
    data = response.get_json()
    assert "Falha ao gerar relatório padrão: Falha no serviço IA Patrimonial" in data['erro'] #

def test_processar_relatorio_api_email_service_error(auth_client, mock_patrimonial_service, mock_email_service):
    """Testa API quando o serviço de e-mail levanta uma exceção mas o patrimonial tem sucesso."""
    mock_patrimonial_service.return_value = "Sucesso Patrimonial"
    mock_email_service.side_effect = Exception("Falha no serviço IA Email")

    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': 'Texto qualquer', 'format_for_email': True})
    assert response.status_code == 200 # Se o patrimonial teve sucesso, o status geral é 200
    data = response.get_json()
    assert data['relatorio_processado'] == "Sucesso Patrimonial"
    assert "Falha ao gerar relatório para e-mail: Falha no serviço IA Email" in data['erro_email'] #