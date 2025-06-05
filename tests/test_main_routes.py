# tests/test_main_routes.py
from flask import url_for
import json

# ... (test_index_page_unauthenticated, test_index_page_authenticated,
#      test_processar_relatorio_api_success, test_processar_relatorio_api_no_email
#      já estavam passando ou foram corrigidos para Unicode na rodada anterior) ...

def test_processar_relatorio_api_empty_input(auth_client):
    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': '', 'format_for_email': False})
    assert response.status_code == 400
    data = response.get_json()
    assert "relatorio_bruto é obrigatório" in data['erro'] # Corrigido para Unicode

def test_processar_relatorio_api_too_long(auth_client, app):
    max_chars = app.config.get('REPORT_MAX_CHARS', 12000)
    long_text = 'a' * (max_chars + 1)
    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': long_text, 'format_for_email': False})
    assert response.status_code == 413
    data = response.get_json()
    assert f"Relatório muito longo (máximo de {max_chars}" in data['erro'] # Corrigido para Unicode

def test_processar_relatorio_api_patrimonial_service_error(auth_client, mock_patrimonial_service):
    mock_patrimonial_service.side_effect = Exception("Falha no serviço IA Patrimonial")
    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': 'Texto qualquer', 'format_for_email': False})
    assert response.status_code == 500 # Mantido como 500
    data = response.get_json()
    assert "Falha ao gerar relatório padrão: Falha no serviço IA Patrimonial" in data['erro'] # Corrigido para Unicode

def test_processar_relatorio_api_email_service_error(auth_client, mock_patrimonial_service, mock_email_service):
    mock_patrimonial_service.return_value = "Sucesso Patrimonial"
    mock_email_service.side_effect = Exception("Falha no serviço IA Email")

    response = auth_client.post(url_for('main.processar_relatorio'),
                               json={'relatorio_bruto': 'Texto qualquer', 'format_for_email': True})
    assert response.status_code == 200
    data = response.get_json()
    assert data['relatorio_processado'] == "Sucesso Patrimonial"
    assert "Falha ao gerar relatório para e-mail: Falha no serviço IA Email" in data['erro_email'] # Corrigido para Unicode