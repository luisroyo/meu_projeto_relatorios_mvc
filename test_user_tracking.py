#!/usr/bin/env python3
"""
Script de teste para verificar o sistema de tracking de usuários.
"""
import requests
import json
from datetime import datetime

# Configurações
BASE_URL = "http://127.0.0.1:5000"
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "123456"

def test_api_login():
    """Testa login via API e verifica se registra no histórico."""
    print("=== Testando Login via API ===")
    
    # Dados de login
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        # Faz login via API
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"Token obtido: {token[:20]}...")
            
            # Testa uma requisição autenticada
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                
                # Testa endpoint que deve registrar atividade
                profile_response = requests.get(
                    f"{BASE_URL}/api/auth/profile",
                    headers=headers
                )
                print(f"Profile Status: {profile_response.status_code}")
                
                # Testa endpoint de ocorrências
                ocorrencias_response = requests.get(
                    f"{BASE_URL}/api/ocorrencias",
                    headers=headers
                )
                print(f"Ocorrências Status: {ocorrencias_response.status_code}")
                
        return response.status_code == 200
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False

def test_web_login():
    """Testa login via web interface."""
    print("\n=== Testando Login via Web ===")
    
    try:
        # Simula login via web (POST para /auth/login)
        session = requests.Session()
        
        # Primeiro acessa a página de login
        login_page = session.get(f"{BASE_URL}/auth/login")
        print(f"Login page status: {login_page.status_code}")
        
        # Simula login (isso pode não funcionar completamente sem CSRF token)
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "remember": False
        }
        
        login_response = session.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            allow_redirects=False
        )
        print(f"Login response status: {login_response.status_code}")
        
        return login_response.status_code in [200, 302]
        
    except Exception as e:
        print(f"Erro no teste web: {e}")
        return False

def check_database():
    """Verifica o estado do banco de dados."""
    print("\n=== Verificando Banco de Dados ===")
    
    try:
        from app import create_app, db
        from app.models.login_history import LoginHistory
        from app.models.user_online import UserOnline
        from datetime import datetime, timedelta
        
        app = create_app()
        with app.app_context():
            hoje = datetime.now().date()
            
            # Verifica logins de hoje
            logins_hoje = LoginHistory.query.filter(
                LoginHistory.success == True,
                db.func.date(LoginHistory.timestamp) == hoje
            ).all()
            
            print(f"Logins bem-sucedidos hoje ({hoje}): {len(logins_hoje)}")
            for login in logins_hoje:
                print(f"  - {login.timestamp} - User ID: {login.user_id} - IP: {login.ip_address}")
            
            # Verifica usuários online
            usuarios_online = UserOnline.get_online_users()
            print(f"\nUsuários online: {len(usuarios_online)}")
            for user in usuarios_online:
                print(f"  - {user[1]} ({user[2]}) - Última atividade: {user[3]}")
            
            # Verifica logins das últimas 24h
            ontem = hoje - timedelta(days=1)
            logins_24h = LoginHistory.query.filter(
                LoginHistory.timestamp >= ontem
            ).order_by(LoginHistory.timestamp.desc()).all()
            
            print(f"\nLogins nas últimas 24h: {len(logins_24h)}")
            for login in logins_24h[:10]:  # Mostra apenas os 10 mais recentes
                status = "✅" if login.success else "❌"
                print(f"  {status} {login.timestamp} - User ID: {login.user_id} - {login.failure_reason or 'Sucesso'}")
                
    except Exception as e:
        print(f"Erro ao verificar banco: {e}")

if __name__ == "__main__":
    print("Iniciando testes de tracking de usuários...")
    print(f"URL Base: {BASE_URL}")
    print(f"Email de teste: {TEST_EMAIL}")
    print("=" * 50)
    
    # Testa login via API
    api_success = test_api_login()
    
    # Testa login via web
    web_success = test_web_login()
    
    # Verifica banco de dados
    check_database()
    
    print("\n" + "=" * 50)
    print("Resumo dos testes:")
    print(f"API Login: {'✅ Sucesso' if api_success else '❌ Falha'}")
    print(f"Web Login: {'✅ Sucesso' if web_success else '❌ Falha'}")
    print("\nVerifique os logs do servidor para mais detalhes.") 