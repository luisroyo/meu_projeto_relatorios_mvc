#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000/api"

def test_rondas_executadas():
    """Testa o endpoint de rondas executadas."""
    print("🧪 Testando API de rondas executadas...")
    
    # Teste 1: Sem filtros de data
    print("\n1️⃣ Teste básico (sem filtros de data):")
    try:
        response = requests.get(f"{BASE_URL}/rondas-esporadicas/executadas?condominio_id=1")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                rondas = data.get("rondas", [])
                print(f"✅ Sucesso! Encontradas {len(rondas)} rondas executadas")
                for ronda in rondas[:3]:  # Mostrar apenas as 3 primeiras
                    print(f"   - ID: {ronda['id']}, Data: {ronda['data_plantao']}, Duração: {ronda.get('duracao_formatada', 'N/A')}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

    # Teste 2: Com filtros de data
    print("\n2️⃣ Teste com filtros de data:")
    try:
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{BASE_URL}/rondas-esporadicas/executadas?condominio_id=1&data_inicio={data_inicio}&data_fim={data_fim}"
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {url}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                rondas = data.get("rondas", [])
                print(f"✅ Sucesso! Encontradas {len(rondas)} rondas executadas no período")
                print(f"Filtros aplicados: {data.get('filtros', {})}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

    # Teste 3: Validação de parâmetros
    print("\n3️⃣ Teste de validação (sem condominio_id):")
    try:
        response = requests.get(f"{BASE_URL}/rondas-esporadicas/executadas")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Validação funcionando corretamente!")
        else:
            print("❌ Validação não funcionou como esperado")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

    # Teste 4: Condomínio inexistente
    print("\n4️⃣ Teste com condomínio inexistente:")
    try:
        response = requests.get(f"{BASE_URL}/rondas-esporadicas/executadas?condominio_id=999")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                rondas = data.get("rondas", [])
                print(f"✅ Sucesso! Encontradas {len(rondas)} rondas (esperado: 0)")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def test_estatisticas_api():
    """Testa o endpoint de estatísticas."""
    print("\n📊 Testando API de estatísticas...")
    try:
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{BASE_URL}/rondas-esporadicas/estatisticas/1?data_inicio={data_inicio}&data_fim={data_fim}"
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {url}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                estatisticas = data.get("estatisticas", {})
                resumo = estatisticas.get("resumo", {})
                print(f"✅ Sucesso! Estatísticas obtidas:")
                print(f"   - Total de rondas: {resumo.get('total_rondas', 0)}")
                print(f"   - Rondas finalizadas: {resumo.get('rondas_finalizadas', 0)}")
                print(f"   - Duração total: {resumo.get('duracao_total_formatada', 'N/A')}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando testes da API de rondas executadas...")
    print("=" * 60)
    
    test_rondas_executadas()
    test_estatisticas_api()
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")
    print("\n💡 Dicas:")
    print("- Certifique-se de que o servidor Flask está rodando")
    print("- Verifique se há dados de teste no banco de dados")
    print("- Se não houver dados, use o script criar_dados_teste.py primeiro") 