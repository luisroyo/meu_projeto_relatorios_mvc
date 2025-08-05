#!/usr/bin/env python3
"""
Teste simples para verificar se o servidor está funcionando.
"""
import requests

def test_server_status():
    """Testa se o servidor está respondendo."""
    print("🔍 Testando Status do Servidor")
    print("=" * 40)
    
    # Teste básico
    try:
        response = requests.get("https://processador-relatorios-ia.onrender.com/")
        print(f"✅ GET / Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro GET /: {e}")
    
    # Teste OPTIONS simples
    try:
        response = requests.options("https://processador-relatorios-ia.onrender.com/api/login")
        print(f"✅ OPTIONS /api/login Status: {response.status_code}")
        print(f"✅ Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ Erro OPTIONS: {e}")
    
    # Teste POST simples
    try:
        response = requests.post("https://processador-relatorios-ia.onrender.com/api/login", 
                               json={"email": "test", "password": "test"})
        print(f"✅ POST /api/login Status: {response.status_code}")
        print(f"✅ Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Erro POST: {e}")

if __name__ == "__main__":
    test_server_status() 