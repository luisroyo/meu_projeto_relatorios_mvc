#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Debug para Gráficos - Verifica números incorretos
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from app import create_app
from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data


def debug_grafico_ocorrencias_por_tipo():
    """Debug específico para o gráfico de ocorrências por tipo"""
    print("🔍 DEBUG: Gráfico Ocorrências por Tipo")
    print("=" * 60)
    
    # Teste 1: Sem filtros
    print("\n1️⃣ TESTE SEM FILTROS:")
    filters_sem = {
        "data_inicio_str": "2024-01-01",
        "data_fim_str": "2024-01-31",
        "supervisor_id": None,
        "condominio_id": None,
        "turno": None,
        "status": None
    }
    
    try:
        result_sem = get_ocorrencia_dashboard_data(filters_sem)
        print(f"   Total de ocorrências: {result_sem.get('total_ocorrencias', 'N/A')}")
        print(f"   Tipos encontrados: {len(result_sem.get('tipo_labels', []))}")
        
        print("   📊 Dados do gráfico:")
        tipo_labels = result_sem.get('tipo_labels', [])
        tipo_data = result_sem.get('ocorrencias_por_tipo_data', [])
        for i, (label, data) in enumerate(zip(tipo_labels, tipo_data)):
            print(f"      {i+1}. {label}: {data}")
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # Teste 2: Com supervisor específico
    print("\n2️⃣ TESTE COM SUPERVISOR ESPECÍFICO:")
    filters_com = {
        "data_inicio_str": "2024-01-01",
        "data_fim_str": "2024-01-31",
        "supervisor_id": 1,  # Testar com supervisor ID 1
        "condominio_id": None,
        "turno": None,
        "status": None
    }
    
    try:
        result_com = get_ocorrencia_dashboard_data(filters_com)
        print(f"   Total de ocorrências: {result_com.get('total_ocorrencias', 'N/A')}")
        print(f"   Tipos encontrados: {len(result_com.get('tipo_labels', []))}")
        
        print("   📊 Dados do gráfico (filtrado por supervisor):")
        tipo_labels = result_com.get('tipo_labels', [])
        tipo_data = result_com.get('ocorrencias_por_tipo_data', [])
        for i, (label, data) in enumerate(zip(tipo_labels, tipo_data)):
            print(f"      {i+1}. {label}: {data}")
            
        # Verificar se há números suspeitos
        for label, data in zip(tipo_labels, tipo_data):
            if data > 1000:  # Números suspeitamente altos
                print(f"      ⚠️  ATENÇÃO: {label} tem {data} ocorrências (número suspeito!)")
                
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # Teste 3: Comparar totais
    print("\n3️⃣ COMPARAÇÃO:")
    try:
        if 'result_sem' in locals() and 'result_com' in locals():
            total_sem = result_sem.get('total_ocorrencias', 0)
            total_com = result_com.get('total_ocorrencias', 0)
            
            print(f"   Total sem filtro: {total_sem}")
            print(f"   Total com supervisor: {total_com}")
            
            if total_com > total_sem:
                print(f"   ❌ PROBLEMA: Total com supervisor ({total_com}) é MAIOR que sem filtro ({total_sem})")
                print(f"      Isso indica um problema na lógica de filtros!")
            elif total_com == total_sem:
                print(f"   ⚠️  ATENÇÃO: Total com supervisor ({total_com}) é IGUAL ao sem filtro ({total_sem})")
                print(f"      O filtro pode não estar funcionando!")
            else:
                print(f"   ✅ OK: Total com supervisor ({total_com}) é menor que sem filtro ({total_sem})")
                
    except Exception as e:
        print(f"   ❌ ERRO na comparação: {e}")


def debug_grafico_ocorrencias_por_condominio():
    """Debug específico para o gráfico de ocorrências por condomínio"""
    print("\n🔍 DEBUG: Gráfico Ocorrências por Condomínio")
    print("=" * 60)
    
    # Teste 1: Sem filtros
    print("\n1️⃣ TESTE SEM FILTROS:")
    filters_sem = {
        "data_inicio_str": "2024-01-01",
        "data_fim_str": "2024-01-31",
        "supervisor_id": None,
        "condominio_id": None,
        "turno": None,
        "status": None
    }
    
    try:
        result_sem = get_ocorrencia_dashboard_data(filters_sem)
        print(f"   Total de ocorrências: {result_sem.get('total_ocorrencias', 'N/A')}")
        print(f"   Condomínios encontrados: {len(result_sem.get('condominio_labels', []))}")
        
        print("   🏢 Dados do gráfico:")
        cond_labels = result_sem.get('condominio_labels', [])
        cond_data = result_sem.get('ocorrencias_por_condominio_data', [])
        for i, (label, data) in enumerate(zip(cond_labels, cond_data)):
            print(f"      {i+1}. {label}: {data}")
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # Teste 2: Com supervisor específico
    print("\n2️⃣ TESTE COM SUPERVISOR ESPECÍFICO:")
    filters_com = {
        "data_inicio_str": "2024-01-01",
        "data_fim_str": "2024-01-31",
        "supervisor_id": 1,  # Testar com supervisor ID 1
        "condominio_id": None,
        "turno": None,
        "status": None
    }
    
    try:
        result_com = get_ocorrencia_dashboard_data(filters_com)
        print(f"   Total de ocorrências: {result_com.get('total_ocorrencias', 'N/A')}")
        print(f"   Condomínios encontrados: {len(result_com.get('condominio_labels', []))}")
        
        print("   🏢 Dados do gráfico (filtrado por supervisor):")
        cond_labels = result_com.get('condominio_labels', [])
        cond_data = result_com.get('ocorrencias_por_condominio_data', [])
        for i, (label, data) in enumerate(zip(cond_labels, cond_data)):
            print(f"      {i+1}. {label}: {data}")
            
        # Verificar se há números suspeitos
        for label, data in zip(cond_labels, cond_data):
            if data > 1000:  # Números suspeitamente altos
                print(f"      ⚠️  ATENÇÃO: {label} tem {data} ocorrências (número suspeito!)")
                
    except Exception as e:
        print(f"   ❌ ERRO: {e}")


def main():
    """Função principal"""
    print("🚀 DEBUG DOS GRÁFICOS - Verificando números incorretos")
    print("=" * 80)
    
    # Criar app Flask para contexto
    app = create_app()
    
    with app.app_context():
        # Debug do gráfico de tipos
        debug_grafico_ocorrencias_por_tipo()
        
        # Debug do gráfico de condomínios
        debug_grafico_ocorrencias_por_condominio()
        
        print("\n" + "=" * 80)
        print("💡 ANÁLISE:")
        print("   - Se os números com supervisor são maiores que sem filtro, há problema na lógica")
        print("   - Se os números são iguais, o filtro não está funcionando")
        print("   - Se há números muito altos (ex: 50 mil), pode haver problema na view ou joins")
        print("   - Verifique se a view VWOcorrenciasDetalhadas está correta")


if __name__ == "__main__":
    main()
