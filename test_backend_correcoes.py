#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000/api"

def test_validacao_horario():
    """Testa a validação de horário (DESABILITADA)."""
    print("⏰ Testando validação de horário (DESABILITADA)...")
    
    # Teste com horário atual (deve passar)
    hora_atual = datetime.now().time()
    hora_atual_str = hora_atual.strftime("%H:%M")
    
    # Teste com horário muito diferente (deve passar também)
    hora_diferente = "03:00"  # 3 da manhã
    
    try:
        # Teste 1: Horário atual
        response = requests.post(f"{BASE_URL}/rondas-esporadicas/validar-horario", json={
            "hora_entrada": hora_atual_str
        })
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                print("✅ Validação de horário funcionando (DESABILITADA)!")
                print(f"   - Horário atual: {data.get('hora_atual')}")
                print(f"   - Horário informado: {data.get('hora_informada')}")
                print(f"   - Observação: {data.get('observacao')}")
            else:
                print(f"❌ Erro na validação: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
        # Teste 2: Horário muito diferente
        response2 = requests.post(f"{BASE_URL}/rondas-esporadicas/validar-horario", json={
            "hora_entrada": hora_diferente
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            if data2.get("sucesso"):
                print("✅ Validação aceita horário muito diferente (DESABILITADA)!")
            else:
                print(f"❌ Erro na validação: {data2.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response2.status_code}")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def test_todas_rondas_esporadicas():
    """Testa o endpoint de todas as rondas esporádicas."""
    print("\n🔄 Testando endpoint de todas as rondas esporádicas...")
    
    try:
        response = requests.get(f"{BASE_URL}/rondas-esporadicas")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                rondas = data.get("rondas", [])
                print(f"✅ Sucesso! Encontradas {len(rondas)} rondas esporádicas")
                print(f"Filtros aplicados: {data.get('filtros', {})}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def test_logradouros_view():
    """Testa o endpoint de logradouros_view."""
    print("\n🏠 Testando endpoint de logradouros_view...")
    
    try:
        response = requests.get(f"{BASE_URL}/logradouros_view")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                logradouros = data.get("logradouros", [])
                print(f"✅ Sucesso! Encontrados {len(logradouros)} logradouros")
                for logradouro in logradouros[:3]:  # Mostrar apenas os 3 primeiros
                    print(f"   - ID: {logradouro['id']}, Nome: {logradouro['nome']}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def test_rondas_executadas():
    """Testa o endpoint de rondas executadas."""
    print("\n✅ Testando endpoint de rondas executadas...")
    
    try:
        response = requests.get(f"{BASE_URL}/rondas-esporadicas/executadas?condominio_id=1")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                rondas = data.get("rondas", [])
                print(f"✅ Sucesso! Encontradas {len(rondas)} rondas executadas")
                print(f"Filtros aplicados: {data.get('filtros', {})}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def test_cors_headers():
    """Testa se os headers CORS estão configurados corretamente."""
    print("\n🌐 Testando headers CORS...")
    
    endpoints = [
        "/api/rondas-esporadicas",
        "/api/rondas-esporadicas/executadas",
        "/api/logradouros_view",
        "/api/condominios"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.options(f"{BASE_URL}{endpoint}")
            print(f"\nEndpoint: {endpoint}")
            print(f"Status Code: {response.status_code}")
            
            # Verificar headers CORS
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            for header in cors_headers:
                value = response.headers.get(header)
                if value:
                    print(f"✅ {header}: {value}")
                else:
                    print(f"❌ {header}: Não encontrado")
                    
        except Exception as e:
            print(f"❌ Erro ao testar {endpoint}: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando testes das correções do backend...")
    print("=" * 60)
    
    test_validacao_horario()
    test_todas_rondas_esporadicas()
    test_logradouros_view()
    test_rondas_executadas()
    test_cors_headers()
    
    print("\n" + "=" * 60)
    print("✅ Testes das correções concluídos!")
    print("\n💡 Resumo das correções implementadas:")
    print("1. ✅ Validação de horário: DESABILITADA (aceita qualquer horário)")
    print("2. ✅ Endpoint /api/rondas-esporadicas: criado com filtros")
    print("3. ✅ Endpoint /api/logradouros_view: criado com CORS")
    print("4. ✅ Endpoint /api/rondas-esporadicas/executadas: já existia")
    print("5. ✅ CORS configurado para todos os endpoints") 