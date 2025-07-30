#!/usr/bin/env python3
"""
Script de teste para APIs de Rondas Esporádicas
"""

import requests
import json
from datetime import datetime, date

# Configurações
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/rondas-esporadicas"

def test_validar_horario():
    """Testa validação de horário de entrada"""
    print("🧪 Testando validação de horário...")
    
    # Teste 1: Horário válido (próximo do atual)
    hora_atual = datetime.now().strftime("%H:%M")
    payload = {"hora_entrada": hora_atual}
    
    response = requests.post(f"{API_BASE}/validar-horario", json=payload)
    print(f"✅ Horário atual ({hora_atual}): {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Resultado: {data}")
    
    # Teste 2: Horário muito diferente
    payload = {"hora_entrada": "23:59"}
    response = requests.post(f"{API_BASE}/validar-horario", json=payload)
    print(f"✅ Horário diferente (23:59): {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Resultado: {data}")

def test_iniciar_ronda():
    """Testa início de ronda esporádica"""
    print("\n🧪 Testando início de ronda...")
    
    payload = {
        "condominio_id": 1,
        "user_id": 1,
        "data_plantao": "2025-01-30",
        "hora_entrada": "14:30",
        "escala_plantao": "06h às 18h",
        "supervisor_id": 2,
        "observacoes": "Teste de ronda esporádica"
    }
    
    response = requests.post(f"{API_BASE}/iniciar", json=payload)
    print(f"✅ Iniciar ronda: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   Ronda criada com ID: {data.get('ronda_id')}")
        return data.get('ronda_id')
    else:
        print(f"   Erro: {response.text}")
        return None

def test_finalizar_ronda(ronda_id):
    """Testa finalização de ronda"""
    if not ronda_id:
        print("❌ Não é possível finalizar ronda sem ID")
        return
    
    print(f"\n🧪 Testando finalização da ronda {ronda_id}...")
    
    payload = {
        "hora_saida": "18:00",
        "observacoes": "Finalização do teste"
    }
    
    response = requests.put(f"{API_BASE}/finalizar/{ronda_id}", json=payload)
    print(f"✅ Finalizar ronda: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Resultado: {data}")
    else:
        print(f"   Erro: {response.text}")

def test_listar_rondas_dia():
    """Testa listagem de rondas do dia"""
    print("\n🧪 Testando listagem de rondas do dia...")
    
    response = requests.get(f"{API_BASE}/do-dia/1/2025-01-30")
    print(f"✅ Listar rondas do dia: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total de rondas: {len(data.get('rondas', []))}")
        for ronda in data.get('rondas', []):
            print(f"   - Ronda {ronda['id']}: {ronda['hora_entrada']} → {ronda['hora_saida']}")
    else:
        print(f"   Erro: {response.text}")

def test_consolidar_turno():
    """Testa consolidação de turno"""
    print("\n🧪 Testando consolidação de turno...")
    
    response = requests.post(f"{API_BASE}/consolidar-turno/1/2025-01-30")
    print(f"✅ Consolidar turno: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total de rondas: {data.get('total_rondas')}")
        print(f"   Duração total: {data.get('duracao_total_minutos')} minutos")
    else:
        print(f"   Erro: {response.text}")

def test_status_consolidacao():
    """Testa status de consolidação"""
    print("\n🧪 Testando status de consolidação...")
    
    response = requests.get(f"{API_BASE}/status-consolidacao/1/2025-01-30")
    print(f"✅ Status consolidação: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        status = data.get('status', {})
        print(f"   Total rondas: {status.get('total_rondas_esporadicas')}")
        print(f"   Finalizadas: {status.get('rondas_finalizadas')}")
        print(f"   Pode consolidar: {status.get('pode_consolidar')}")
        print(f"   Já consolidado: {status.get('ja_consolidado')}")
    else:
        print(f"   Erro: {response.text}")

def test_processo_completo():
    """Testa processo completo de consolidação"""
    print("\n🧪 Testando processo completo...")
    
    response = requests.post(f"{API_BASE}/processo-completo/1/2025-01-30")
    print(f"✅ Processo completo: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        resumo = data.get('resumo', {})
        print(f"   WhatsApp enviado: {resumo.get('whatsapp_enviado')}")
        print(f"   Ronda principal ID: {resumo.get('ronda_principal_id')}")
        print(f"   Rondas processadas: {resumo.get('rondas_marcadas_processadas')}")
    else:
        print(f"   Erro: {response.text}")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes das APIs de Rondas Esporádicas")
    print("=" * 60)
    
    try:
        # Teste 1: Validação de horário
        test_validar_horario()
        
        # Teste 2: Iniciar ronda
        ronda_id = test_iniciar_ronda()
        
        # Teste 3: Finalizar ronda
        test_finalizar_ronda(ronda_id)
        
        # Teste 4: Listar rondas do dia
        test_listar_rondas_dia()
        
        # Teste 5: Status de consolidação
        test_status_consolidacao()
        
        # Teste 6: Consolidar turno
        test_consolidar_turno()
        
        # Teste 7: Processo completo
        test_processo_completo()
        
        print("\n✅ Todos os testes foram executados!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor Flask")
        print("   Certifique-se de que o servidor está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    main() 