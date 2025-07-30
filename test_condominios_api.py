#!/usr/bin/env python3
"""
Script para testar a API de condomínios
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_listar_condominios():
    """Testa a API de listagem de condomínios"""
    print("🧪 Testando API de condomínios...")
    
    try:
        # Teste 1: Listar condomínios
        print("\n1️⃣ Testando GET /condominios")
        response = requests.get(f"{BASE_URL}/condominios")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                condominios = data.get("condominios", [])
                print(f"✅ Sucesso! Encontrados {len(condominios)} condomínios:")
                for cond in condominios:
                    print(f"   - ID: {cond['id']}, Nome: {cond['nome']}")
            else:
                print(f"❌ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor Flask está rodando.")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

def test_condominio_especifico(condominio_id):
    """Testa buscar um condomínio específico (se a API existir)"""
    print(f"\n2️⃣ Testando busca de condomínio ID: {condominio_id}")
    
    try:
        # Primeiro vamos listar todos para ver se o ID existe
        response = requests.get(f"{BASE_URL}/condominios")
        if response.status_code == 200:
            data = response.json()
            if data.get("sucesso"):
                condominios = data.get("condominios", [])
                condominio_encontrado = None
                
                for cond in condominios:
                    if cond['id'] == condominio_id:
                        condominio_encontrado = cond
                        break
                
                if condominio_encontrado:
                    print(f"✅ Condomínio encontrado: {condominio_encontrado['nome']}")
                else:
                    print(f"❌ Condomínio com ID {condominio_id} não encontrado")
                    print("Condomínios disponíveis:")
                    for cond in condominios:
                        print(f"   - ID: {cond['id']}, Nome: {cond['nome']}")
            else:
                print(f"❌ Erro ao listar condomínios: {data.get('message')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando testes da API de condomínios...")
    print("=" * 50)
    
    # Teste básico
    test_listar_condominios()
    
    # Teste com ID específico
    test_condominio_especifico(1)
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!") 