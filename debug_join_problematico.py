#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para identificar o JOIN problemático que está causando produto cartesiano
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from app import create_app
from app import db
from app.models import VWOcorrenciasDetalhadas
from app.services import ocorrencia_service
from sqlalchemy import func, text


def testar_query_evolucao_diaria():
    """Testa especificamente a query de evolução diária"""
    print("🔍 TESTANDO QUERY DE EVOLUÇÃO DIÁRIA")
    print("=" * 60)
    
    try:
        # Teste 1: Query simples sem filtros
        print("\n1️⃣ QUERY SIMPLES SEM FILTROS:")
        query_simples = db.session.query(
            func.date(VWOcorrenciasDetalhadas.data_hora_ocorrencia),
            VWOcorrenciasDetalhadas.turno,
            func.count(VWOcorrenciasDetalhadas.id)
        ).filter(
            VWOcorrenciasDetalhadas.turno.isnot(None)
        )
        
        print(f"   Query SQL: {query_simples}")
        print(f"   Column descriptions: {query_simples.column_descriptions}")
        
        # Teste 2: Query com filtros de data
        print("\n2️⃣ QUERY COM FILTROS DE DATA:")
        from datetime import datetime, timezone
        julho_2025 = datetime(2025, 7, 1, tzinfo=timezone.utc)
        julho_2025_fim = datetime(2025, 7, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        query_com_data = query_simples.filter(
            VWOcorrenciasDetalhadas.data_hora_ocorrencia >= julho_2025,
            VWOcorrenciasDetalhadas.data_hora_ocorrencia <= julho_2025_fim
        )
        
        print(f"   Query com data: {query_com_data}")
        
        # Teste 3: Query com apply_ocorrencia_filters
        print("\n3️⃣ QUERY COM APPLY_OCORRENCIA_FILTERS:")
        filters = {
            "data_inicio_str": "2025-07-01",
            "data_fim_str": "2025-07-31"
        }
        
        query_com_filtros = ocorrencia_service.apply_ocorrencia_filters(
            query_simples, filters
        )
        
        print(f"   Query com filtros: {query_com_filtros}")
        
        # Teste 4: Executar a query para ver o resultado
        print("\n4️⃣ EXECUTANDO QUERY:")
        try:
            resultado = query_com_filtros.group_by(
                func.date(VWOcorrenciasDetalhadas.data_hora_ocorrencia),
                VWOcorrenciasDetalhadas.turno
            ).order_by(func.date(VWOcorrenciasDetalhadas.data_hora_ocorrencia)).all()
            
            print(f"   Total de registros: {len(resultado)}")
            print(f"   Primeiros 5 registros:")
            for i, (data, turno, count) in enumerate(resultado[:5]):
                print(f"      {i+1}. Data: {data}, Turno: {turno}, Count: {count}")
                
            # Verificar se há números absurdos
            for data, turno, count in resultado:
                if count > 1000:
                    print(f"      ⚠️  ATENÇÃO: Data {data}, Turno {turno} tem {count} ocorrências (número suspeito!)")
                    
        except Exception as e:
            print(f"   ❌ ERRO ao executar: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()


def testar_deteccao_view():
    """Testa a detecção automática de view vs tabela"""
    print("\n🔍 TESTANDO DETECÇÃO DE VIEW VS TABELA")
    print("=" * 60)
    
    try:
        # Teste 1: Query da view
        print("\n1️⃣ QUERY DA VIEW:")
        query_view = db.session.query(VWOcorrenciasDetalhadas)
        print(f"   Query: {query_view}")
        print(f"   Column descriptions: {query_view.column_descriptions}")
        
        # Verificar se a detecção está funcionando
        is_view = hasattr(query_view.column_descriptions[0]['type'], '__tablename__') and \
                  query_view.column_descriptions[0]['type'].__tablename__ == 'vw_ocorrencias_detalhadas'
        
        print(f"   É view? {is_view}")
        if query_view.column_descriptions:
            print(f"   Tablename: {query_view.column_descriptions[0]['type'].__tablename__}")
        
        # Teste 2: Query com count
        print("\n2️⃣ QUERY COM COUNT:")
        query_count = db.session.query(
            VWOcorrenciasDetalhadas.tipo,
            func.count(VWOcorrenciasDetalhadas.id)
        )
        
        print(f"   Query: {query_count}")
        print(f"   Column descriptions: {query_count.column_descriptions}")
        
        # Verificar se a detecção está funcionando
        is_view_count = hasattr(query_count.column_descriptions[0]['type'], '__tablename__') and \
                       query_count.column_descriptions[0]['type'].__tablename__ == 'vw_ocorrencias_detalhadas'
        
        print(f"   É view? {is_view_count}")
        if query_count.column_descriptions:
            print(f"   Tablename: {query_count.column_descriptions[0]['type'].__tablename__}")
            
    except Exception as e:
        print(f"❌ ERRO na detecção: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Função principal"""
    print("🚀 DEBUG DO JOIN PROBLEMÁTICO")
    print("=" * 80)
    
    # Criar app Flask para contexto
    app = create_app()
    
    with app.app_context():
        # Testar query de evolução diária
        testar_query_evolucao_diaria()
        
        # Testar detecção de view
        testar_deteccao_view()
        
        print("\n" + "=" * 80)
        print("💡 ANÁLISE:")
        print("   - Se a detecção de view não está funcionando, os filtros podem estar incorretos")
        print("   - Se há JOIN implícito, pode ser na função apply_ocorrencia_filters")
        print("   - Verifique se a view está sendo detectada corretamente")


if __name__ == "__main__":
    main()
