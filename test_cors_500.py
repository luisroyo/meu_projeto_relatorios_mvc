#!/usr/bin/env python3
"""
Teste específico para verificar se o erro 500 no preflight CORS foi resolvido.
"""
import requests

def test_cors_preflight_500():
    """Testa se o preflight CORS não retorna erro 500."""
    print("🔍 Testando Preflight CORS - Verificando Erro 500")
    print("=" * 60)
    
    url = "https://processador-relatorios-ia.onrender.com/api/login"
    headers = {
        'Origin': 'https://ocorrencias-master-app.onrender.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
    }
    
    try:
        # Teste OPTIONS (preflight)
        response = requests.options(url, headers=headers)
        print(f"✅ OPTIONS Status Code: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ ERRO 500 DETECTADO - Preflight ainda está falhando!")
            return False
        elif response.status_code in [200, 204]:
            print("✅ Preflight funcionando - Status correto!")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
        
        # Verificar cabeçalhos CORS
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_methods = response.headers.get('Access-Control-Allow-Methods')
        cors_headers = response.headers.get('Access-Control-Allow-Headers')
        
        print(f"✅ Access-Control-Allow-Origin: {cors_origin}")
        print(f"✅ Access-Control-Allow-Methods: {cors_methods}")
        print(f"✅ Access-Control-Allow-Headers: {cors_headers}")
        
        if cors_origin == 'https://ocorrencias-master-app.onrender.com':
            print("🎉 CORS configurado corretamente!")
            return True
        else:
            print("⚠️  CORS não está configurado corretamente")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_post_request():
    """Testa requisição POST após preflight."""
    print("\n🔍 Testando Requisição POST")
    print("=" * 30)
    
    url = "https://processador-relatorios-ia.onrender.com/api/login"
    headers = {
        'Origin': 'https://ocorrencias-master-app.onrender.com',
        'Content-Type': 'application/json'
    }
    data = {'email': 'test@example.com', 'password': 'test123'}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"✅ POST Status Code: {response.status_code}")
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        print(f"✅ Access-Control-Allow-Origin: {cors_origin}")
        
        if response.status_code in [200, 401, 400]:
            print("✅ Requisição POST funcionando!")
            return True
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição POST: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Teste de Correção do Erro 500 no CORS")
    print("=" * 60)
    
    preflight_ok = test_cors_preflight_500()
    post_ok = test_post_request()
    
    print("\n" + "=" * 60)
    if preflight_ok and post_ok:
        print("🎉 SUCESSO: Erro 500 corrigido! CORS funcionando perfeitamente!")
    else:
        print("❌ PROBLEMA: Ainda há issues com CORS")
    
    print("=" * 60) 