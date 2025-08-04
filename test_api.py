#!/usr/bin/env python3
"""
Script para testar as APIs do sistema de gestão de segurança.
"""

import requests
import json
import sys
from datetime import datetime

# Configurações
API_BASE_URL = "http://localhost:5000/api"
TEST_EMAIL = "luisroyo25@gmail.com"  # Substitua por um email válido do seu banco
TEST_PASSWORD = "dev123"  # Substitua por uma senha válida

def print_section(title):
    """Imprime uma seção de teste."""
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print(f"{'='*50}")

def print_success(message):
    """Imprime uma mensagem de sucesso."""
    print(f"✅ {message}")

def print_error(message):
    """Imprime uma mensagem de erro."""
    print(f"❌ {message}")

def print_info(message):
    """Imprime uma mensagem informativa."""
    print(f"ℹ️  {message}")

def test_auth_login():
    """Testa o endpoint de login."""
    print_section("Testando Login")
    
    url = f"{API_BASE_URL}/auth/login"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Login realizado com sucesso!")
            print_info(f"Token recebido: {result['access_token'][:50]}...")
            print_info(f"Usuário: {result['user']['username']}")
            print_info(f"Email: {result['user']['email']}")
            print_info(f"Admin: {result['user']['is_admin']}")
            return result['access_token']
        else:
            print_error(f"Erro no login: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error("Erro de conexão. Verifique se o backend está rodando em http://localhost:5000")
        return None
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return None

def test_auth_profile(token):
    """Testa o endpoint de perfil do usuário."""
    print_section("Testando Perfil do Usuário")
    
    url = f"{API_BASE_URL}/auth/profile"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Perfil carregado com sucesso!")
            print_info(f"ID: {result['id']}")
            print_info(f"Username: {result['username']}")
            print_info(f"Email: {result['email']}")
            print_info(f"Admin: {result['is_admin']}")
            print_info(f"Supervisor: {result['is_supervisor']}")
            print_info(f"Aprovado: {result['is_approved']}")
        else:
            print_error(f"Erro ao carregar perfil: {response.text}")
            
    except Exception as e:
        print_error(f"Erro inesperado: {e}")

def test_dashboard_stats(token):
    """Testa o endpoint de estatísticas do dashboard."""
    print_section("Testando Estatísticas do Dashboard")
    
    url = f"{API_BASE_URL}/dashboard/stats"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            stats = result['stats']
            user = result['user']
            
            print_success("Estatísticas carregadas com sucesso!")
            print_info(f"Usuário: {user['username']}")
            print_info(f"Total de Ocorrências: {stats['total_ocorrencias']}")
            print_info(f"Total de Rondas: {stats['total_rondas']}")
            print_info(f"Total de Condomínios: {stats['total_condominios']}")
            print_info(f"Rondas em Andamento: {stats['rondas_em_andamento']}")
            print_info(f"Ocorrências (30 dias): {stats['ocorrencias_ultimo_mes']}")
            print_info(f"Rondas (30 dias): {stats['rondas_ultimo_mes']}")
        else:
            print_error(f"Erro ao carregar estatísticas: {response.text}")
            
    except Exception as e:
        print_error(f"Erro inesperado: {e}")

def test_dashboard_recent_ocorrencias(token):
    """Testa o endpoint de ocorrências recentes."""
    print_section("Testando Ocorrências Recentes")
    
    url = f"{API_BASE_URL}/dashboard/recent-ocorrencias"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ocorrencias = result['ocorrencias']
            
            print_success(f"Ocorrências recentes carregadas: {len(ocorrencias)}")
            
            for i, ocorrencia in enumerate(ocorrencias[:3], 1):  # Mostra apenas as 3 primeiras
                print_info(f"Ocorrência {i}:")
                print_info(f"  - Tipo: {ocorrencia['tipo']}")
                print_info(f"  - Condomínio: {ocorrencia['condominio']}")
                print_info(f"  - Data: {ocorrencia['data']}")
                print_info(f"  - Descrição: {ocorrencia['descricao']}")
        else:
            print_error(f"Erro ao carregar ocorrências: {response.text}")
            
    except Exception as e:
        print_error(f"Erro inesperado: {e}")

def test_dashboard_recent_rondas(token):
    """Testa o endpoint de rondas recentes."""
    print_section("Testando Rondas Recentes")
    
    url = f"{API_BASE_URL}/dashboard/recent-rondas"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            rondas = result['rondas']
            
            print_success(f"Rondas recentes carregadas: {len(rondas)}")
            
            for i, ronda in enumerate(rondas[:3], 1):  # Mostra apenas as 3 primeiras
                print_info(f"Ronda {i}:")
                print_info(f"  - Condomínio: {ronda['condominio']}")
                print_info(f"  - Data: {ronda['data_plantao']}")
                print_info(f"  - Escala: {ronda['escala_plantao']}")
                print_info(f"  - Status: {ronda['status']}")
                print_info(f"  - Total de Rondas: {ronda['total_rondas']}")
        else:
            print_error(f"Erro ao carregar rondas: {response.text}")
            
    except Exception as e:
        print_error(f"Erro inesperado: {e}")

def test_invalid_token():
    """Testa o comportamento com token inválido."""
    print_section("Testando Token Inválido")
    
    url = f"{API_BASE_URL}/auth/profile"
    headers = {"Authorization": "Bearer token_invalido"}
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print_success("Token inválido rejeitado corretamente!")
            result = response.json()
            print_info(f"Erro: {result.get('error', 'N/A')}")
        else:
            print_error("Token inválido não foi rejeitado como esperado")
            
    except Exception as e:
        print_error(f"Erro inesperado: {e}")

def test_cors():
    """Testa se o CORS está configurado corretamente."""
    print_section("Testando Configuração CORS")
    
    url = f"{API_BASE_URL}/auth/login"
    
    try:
        # Testa requisição OPTIONS (preflight)
        response = requests.options(url)
        print_info(f"OPTIONS Status Code: {response.status_code}")
        
        if response.status_code in [200, 204]:
            print_success("CORS preflight funcionando!")
            print_info(f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'N/A')}")
            print_info(f"Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'N/A')}")
            print_info(f"Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'N/A')}")
        else:
            print_error("CORS preflight não está funcionando corretamente")
            
    except Exception as e:
        print_error(f"Erro ao testar CORS: {e}")

def main():
    """Função principal que executa todos os testes."""
    print("🚀 Iniciando testes das APIs do Sistema de Gestão de Segurança")
    print(f"📡 URL Base: {API_BASE_URL}")
    print(f"👤 Usuário de teste: {TEST_EMAIL}")
    
    # Teste de CORS
    test_cors()
    
    # Teste de login
    token = test_auth_login()
    
    if token:
        # Testes que requerem autenticação
        test_auth_profile(token)
        test_dashboard_stats(token)
        test_dashboard_recent_ocorrencias(token)
        test_dashboard_recent_rondas(token)
    else:
        print_error("Não foi possível obter token. Pulando testes que requerem autenticação.")
    
    # Teste de token inválido
    test_invalid_token()
    
    print_section("Resumo dos Testes")
    print_success("Testes concluídos!")
    print_info("Para testar o frontend, abra frontend/index.html no navegador")
    print_info("ou execute: cd frontend && python -m http.server 8081")

if __name__ == "__main__":
    main() 