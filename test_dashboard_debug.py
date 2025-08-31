#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Debug para Dashboard de Ocorrências
Testa e verifica as informações fornecidas pelos gráficos
"""

import sys
import os
from datetime import datetime, date

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from app import create_app
from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data


def test_dashboard_basic():
    """Testa o dashboard básico sem filtros específicos"""
    print("🔍 TESTANDO DASHBOARD BÁSICO (sem supervisor)")
    print("=" * 60)
    
    filters = {
        "data_inicio_str": "2024-01-01",
        "data_fim_str": "2024-01-31",
        "supervisor_id": None,
        "condominio_id": None,
        "turno": None,
        "status": None
    }
    
    try:
        result = get_ocorrencia_dashboard_data(filters)
        
        print(f"✅ Total de ocorrências: {result.get('total_ocorrencias', 'N/A')}")
        print(f"✅ Ocorrências abertas: {result.get('ocorrencias_abertas', 'N/A')}")
        print(f"✅ Tipo mais comum: {result.get('tipo_mais_comum', 'N/A')}")
        print(f"✅ Supervisor: {result.get('kpi_supervisor_label', 'N/A')} - {result.get('kpi_supervisor_name', 'N/A')}")
        
        print("\n📊 GRÁFICO - Ocorrências por Tipo:")
        tipo_labels = result.get('tipo_labels', [])
        tipo_data = result.get('ocorrencias_por_tipo_data', [])
        for i, (label, data) in enumerate(zip(tipo_labels, tipo_data)):
            print(f"   {i+1}. {label}: {data}")
        
        print("\n🏢 GRÁFICO - Ocorrências por Condomínio:")
        cond_labels = result.get('condominio_labels', [])
        cond_data = result.get('ocorrencias_por_condominio_data', [])
        for i, (label, data) in enumerate(zip(cond_labels, cond_data)):
            print(f"   {i+1}. {label}: {data}")
        
        print("\n📈 INFORMAÇÕES DO PERÍODO:")
        periodo_info = result.get('periodo_info', {})
        print(f"   Dias com dados: {periodo_info.get('dias_com_dados', 'N/A')}")
        print(f"   Período solicitado: {periodo_info.get('periodo_solicitado_dias', 'N/A')}")
        print(f"   Cobertura: {periodo_info.get('cobertura_periodo', 'N/A')}%")
        
        print("\n🔄 COMPARAÇÃO COM PERÍODO ANTERIOR:")
        comparacao = result.get('comparacao_periodo', {})
        print(f"   Total atual: {comparacao.get('total_atual', 'N/A')}")
        print(f"   Total anterior: {comparacao.get('total_anterior', 'N/A')}")
        print(f"   Variação: {comparacao.get('variacao_percentual', 'N/A')}%")
        print(f"   Status: {comparacao.get('status_text', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no dashboard básico: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_with_supervisor():
    """Testa o dashboard com supervisor específico"""
    print("\n🔍 TESTANDO DASHBOARD COM SUPERVISOR ESPECÍFICO")
    print("=" * 60)
    
    # Testar com diferentes supervisores
    supervisor_ids = [1, 2, 3]  # IDs de supervisores para testar
    
    for supervisor_id in supervisor_ids:
        print(f"\n👤 Testando Supervisor ID: {supervisor_id}")
        print("-" * 40)
        
        filters = {
            "data_inicio_str": "2024-01-01",
            "data_fim_str": "2024-01-31",
            "supervisor_id": supervisor_id,
            "condominio_id": None,
            "turno": None,
            "status": None
        }
        
        try:
            result = get_ocorrencia_dashboard_data(filters)
            
            print(f"✅ Total de ocorrências: {result.get('total_ocorrencias', 'N/A')}")
            print(f"✅ Ocorrências abertas: {result.get('ocorrencias_abertas', 'N/A')}")
            print(f"✅ Supervisor: {result.get('kpi_supervisor_label', 'N/A')} - {result.get('kpi_supervisor_name', 'N/A')}")
            
            print("\n📊 GRÁFICO - Ocorrências por Tipo (Filtrado):")
            tipo_labels = result.get('tipo_labels', [])
            tipo_data = result.get('ocorrencias_por_tipo_data', [])
            for i, (label, data) in enumerate(zip(tipo_labels, tipo_data)):
                print(f"   {i+1}. {label}: {data}")
            
            print("\n🏢 GRÁFICO - Ocorrências por Condomínio (Filtrado):")
            cond_labels = result.get('condominio_labels', [])
            cond_data = result.get('ocorrencias_por_condominio_data', [])
            for i, (label, data) in enumerate(zip(cond_labels, cond_data)):
                print(f"   {i+1}. {label}: {data}")
            
            print("\n📈 INFORMAÇÕES DO PERÍODO (Ajustadas para Supervisor):")
            periodo_info = result.get('periodo_info', {})
            print(f"   Dias com dados: {periodo_info.get('dias_com_dados', 'N/A')}")
            print(f"   Período solicitado: {periodo_info.get('periodo_solicitado_dias', 'N/A')}")
            print(f"   Cobertura: {periodo_info.get('cobertura_periodo', 'N/A')}%")
            
            # Verificar se a cobertura está correta para supervisor
            if supervisor_id and periodo_info.get('cobertura_periodo') == 100.0:
                print("   ✅ Cobertura 100% - Supervisor selecionado corretamente")
            elif supervisor_id and periodo_info.get('cobertura_periodo') != 100.0:
                print(f"   ⚠️  Cobertura {periodo_info.get('cobertura_periodo')}% - Pode haver problema")
            
        except Exception as e:
            print(f"❌ ERRO com supervisor {supervisor_id}: {e}")
            continue


def test_dashboard_filters():
    """Testa diferentes combinações de filtros"""
    print("\n🔍 TESTANDO DIFERENTES COMBINAÇÕES DE FILTROS")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Filtro por Condomínio",
            "filters": {
                "data_inicio_str": "2024-01-01",
                "data_fim_str": "2024-01-31",
                "supervisor_id": None,
                "condominio_id": 1,
                "turno": None,
                "status": None
            }
        },
        {
            "name": "Filtro por Turno",
            "filters": {
                "data_inicio_str": "2024-01-01",
                "data_fim_str": "2024-01-31",
                "supervisor_id": None,
                "condominio_id": None,
                "turno": "Diurno Par",
                "status": None
            }
        },
        {
            "name": "Filtro por Status",
            "filters": {
                "data_inicio_str": "2024-01-01",
                "data_fim_str": "2024-01-31",
                "supervisor_id": None,
                "condominio_id": None,
                "turno": None,
                "status": "Registrada"
            }
        },
        {
            "name": "Filtro Combinado",
            "filters": {
                "data_inicio_str": "2024-01-01",
                "data_fim_str": "2024-01-31",
                "supervisor_id": 1,
                "condominio_id": 1,
                "turno": "Diurno Par",
                "status": "Registrada"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}")
        print("-" * 40)
        
        try:
            result = get_ocorrencia_dashboard_data(test_case['filters'])
            
            print(f"✅ Total de ocorrências: {result.get('total_ocorrencias', 'N/A')}")
            print(f"✅ Ocorrências abertas: {result.get('ocorrencias_abertas', 'N/A')}")
            
            # Verificar se os gráficos têm dados
            tipo_count = len(result.get('tipo_labels', []))
            cond_count = len(result.get('condominio_labels', []))
            
            print(f"📊 Tipos de ocorrência encontrados: {tipo_count}")
            print(f"🏢 Condomínios encontrados: {cond_count}")
            
            if tipo_count == 0:
                print("   ⚠️  Nenhum tipo de ocorrência encontrado - verificar filtros")
            if cond_count == 0:
                print("   ⚠️  Nenhum condomínio encontrado - verificar filtros")
                
        except Exception as e:
            print(f"❌ ERRO: {e}")
            continue


def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO DASHBOARD DE OCORRÊNCIAS")
    print("=" * 80)
    
    # Criar app Flask para contexto
    app = create_app()
    
    with app.app_context():
        # Teste 1: Dashboard básico
        success1 = test_dashboard_basic()
        
        # Teste 2: Dashboard com supervisor
        test_dashboard_with_supervisor()
        
        # Teste 3: Diferentes filtros
        test_dashboard_filters()
        
        print("\n" + "=" * 80)
        if success1:
            print("✅ TESTES CONCLUÍDOS - Verifique os resultados acima")
        else:
            print("❌ ALGUNS TESTES FALHARAM - Verifique os erros acima")
        
        print("\n💡 DICAS DE DEBUG:")
        print("   - Verifique se o banco de dados está acessível")
        print("   - Confirme se as tabelas têm dados")
        print("   - Verifique se os filtros estão sendo aplicados corretamente")
        print("   - Compare os números dos gráficos com os KPIs principais")


if __name__ == "__main__":
    main()
