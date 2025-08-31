#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Debug do Banco de Dados - Verifica dados reais
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from app import create_app
from app import db
from app.models import Ocorrencia, User, Condominio, OcorrenciaTipo
from app.models.vw_ocorrencias_detalhadas import VWOcorrenciasDetalhadas
from sqlalchemy import func, text


def verificar_dados_reais():
    """Verifica dados reais nas tabelas"""
    print("🔍 VERIFICANDO DADOS REAIS NO BANCO")
    print("=" * 60)
    
    try:
        # 1. Verificar tabela Ocorrencia
        print("\n1️⃣ TABELA OCORRÊNCIA:")
        total_ocorrencias = Ocorrencia.query.count()
        print(f"   Total de ocorrências: {total_ocorrencias}")
        
        if total_ocorrencias > 0:
            # Verificar algumas ocorrências
            ocorrencias = Ocorrencia.query.limit(3).all()
            for i, oc in enumerate(ocorrencias):
                print(f"   Ocorrência {i+1}: ID={oc.id}, Data={oc.data_hora_ocorrencia}, Status={oc.status}")
                if oc.supervisor_id:
                    print(f"      Supervisor ID: {oc.supervisor_id}")
                if oc.condominio_id:
                    print(f"      Condomínio ID: {oc.condominio_id}")
        else:
            print("   ⚠️  NENHUMA OCORRÊNCIA ENCONTRADA!")
        
        # 2. Verificar view VWOcorrenciasDetalhadas
        print("\n2️⃣ VIEW VW_OCORRÊNCIAS_DETALHADAS:")
        try:
            total_view = VWOcorrenciasDetalhadas.query.count()
            print(f"   Total na view: {total_view}")
            
            if total_view > 0:
                # Verificar algumas ocorrências da view
                ocorrencias_view = VWOcorrenciasDetalhadas.query.limit(3).all()
                for i, oc in enumerate(ocorrencias_view):
                    print(f"   View {i+1}: ID={oc.id}, Data={oc.data_hora_ocorrencia}, Status={oc.status}")
                    print(f"      Supervisor: {oc.supervisor}, Condomínio: {oc.condominio}, Tipo: {oc.tipo}")
            else:
                print("   ⚠️  NENHUMA OCORRÊNCIA NA VIEW!")
                
        except Exception as e:
            print(f"   ❌ ERRO ao acessar view: {e}")
        
        # 3. Verificar usuários/supervisores
        print("\n3️⃣ USUÁRIOS/SUPERVISORES:")
        total_users = User.query.count()
        print(f"   Total de usuários: {total_users}")
        
        if total_users > 0:
            users = User.query.limit(3).all()
            for i, user in enumerate(users):
                print(f"   Usuário {i+1}: ID={user.id}, Username={user.username}")
        
        # 4. Verificar condomínios
        print("\n4️⃣ CONDOMÍNIOS:")
        total_condominios = Condominio.query.count()
        print(f"   Total de condomínios: {total_condominios}")
        
        if total_condominios > 0:
            condominios = Condominio.query.limit(3).all()
            for i, cond in enumerate(condominios):
                print(f"   Condomínio {i+1}: ID={cond.id}, Nome={cond.nome}")
        
        # 5. Verificar tipos de ocorrência
        print("\n5️⃣ TIPOS DE OCORRÊNCIA:")
        total_tipos = OcorrenciaTipo.query.count()
        print(f"   Total de tipos: {total_tipos}")
        
        if total_tipos > 0:
            tipos = OcorrenciaTipo.query.limit(3).all()
            for i, tipo in enumerate(tipos):
                print(f"   Tipo {i+1}: ID={tipo.id}, Nome={tipo.nome}")
        
        # 6. Verificar SQL direto na view
        print("\n6️⃣ SQL DIRETO NA VIEW:")
        try:
            # Executar SQL direto para ver se a view funciona
            result = db.session.execute(text("SELECT COUNT(*) FROM vw_ocorrencias_detalhadas"))
            count = result.scalar()
            print(f"   SQL direto - Total: {count}")
            
            # Verificar estrutura da view
            result = db.session.execute(text("SELECT * FROM vw_ocorrencias_detalhadas LIMIT 1"))
            row = result.fetchone()
            if row:
                print(f"   Estrutura da view: {row}")
            else:
                print("   ⚠️  View não retorna dados!")
                
        except Exception as e:
            print(f"   ❌ ERRO no SQL direto: {e}")
            
        return total_ocorrencias
            
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        return 0


def verificar_filtros_simples(total_ocorrencias):
    """Verifica filtros simples para identificar problemas"""
    print("\n🔍 VERIFICANDO FILTROS SIMPLES")
    print("=" * 60)
    
    try:
        # 1. Filtro por data simples
        print("\n1️⃣ FILTRO POR DATA:")
        from datetime import datetime, timezone
        
        # Buscar ocorrências de hoje
        hoje = datetime.now(timezone.utc).date()
        ocorrencias_hoje = Ocorrencia.query.filter(
            func.date(Ocorrencia.data_hora_ocorrencia) == hoje
        ).count()
        print(f"   Ocorrências hoje ({hoje}): {ocorrencias_hoje}")
        
        # Buscar ocorrências deste mês
        from datetime import date
        mes_atual = date.today().replace(day=1)
        ocorrencias_mes = Ocorrencia.query.filter(
            Ocorrencia.data_hora_ocorrencia >= mes_atual
        ).count()
        print(f"   Ocorrências este mês: {ocorrencias_mes}")
        
        # Buscar ocorrências de julho 2025 (onde sabemos que há dados)
        from datetime import datetime
        julho_2025 = datetime(2025, 7, 1, tzinfo=timezone.utc)
        julho_2025_fim = datetime(2025, 7, 31, 23, 59, 59, tzinfo=timezone.utc)
        ocorrencias_julho = Ocorrencia.query.filter(
            Ocorrencia.data_hora_ocorrencia >= julho_2025,
            Ocorrencia.data_hora_ocorrencia <= julho_2025_fim
        ).count()
        print(f"   Ocorrências julho 2025: {ocorrencias_julho}")
        
        # 2. Filtro por supervisor simples
        print("\n2️⃣ FILTRO POR SUPERVISOR:")
        if total_ocorrencias > 0:
            # Pegar primeiro supervisor que tem ocorrências
            supervisor_com_ocorrencias = db.session.query(Ocorrencia.supervisor_id).filter(
                Ocorrencia.supervisor_id.isnot(None)
            ).first()
            
            if supervisor_com_ocorrencias:
                supervisor_id = supervisor_com_ocorrencias[0]
                print(f"   Testando com supervisor ID: {supervisor_id}")
                
                # Contar ocorrências deste supervisor
                ocorrencias_supervisor = Ocorrencia.query.filter(
                    Ocorrencia.supervisor_id == supervisor_id
                ).count()
                print(f"   Ocorrências deste supervisor: {ocorrencias_supervisor}")
                
                # Verificar se há dados na view para este supervisor
                try:
                    supervisor_user = User.query.get(supervisor_id)
                    if supervisor_user:
                        ocorrencias_view_supervisor = VWOcorrenciasDetalhadas.query.filter(
                            VWOcorrenciasDetalhadas.supervisor == supervisor_user.username
                        ).count()
                        print(f"   Ocorrências na view para este supervisor: {ocorrencias_view_supervisor}")
                except Exception as e:
                    print(f"   ❌ ERRO ao verificar view: {e}")
            else:
                print("   ⚠️  Nenhum supervisor encontrado com ocorrências")
        
        # 3. Verificar se há problemas de timezone
        print("\n3️⃣ VERIFICAÇÃO DE TIMEZONE:")
        if total_ocorrencias > 0:
            # Pegar primeira ocorrência
            primeira_oc = Ocorrencia.query.first()
            if primeira_oc:
                print(f"   Primeira ocorrência - Data: {primeira_oc.data_hora_ocorrencia}")
                print(f"   Timezone info: {primeira_oc.data_hora_ocorrencia.tzinfo}")
                
    except Exception as e:
        print(f"❌ ERRO nos filtros simples: {e}")
        import traceback
        traceback.print_exc()


def testar_dashboard_com_datas_reais():
    """Testa o dashboard com datas reais onde há dados"""
    print("\n🔍 TESTANDO DASHBOARD COM DATAS REAIS")
    print("=" * 60)
    
    try:
        from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data
        
        # Teste 1: Com datas de julho 2025 (onde sabemos que há dados)
        print("\n1️⃣ TESTE COM JULHO 2025:")
        filters_julho = {
            "data_inicio_str": "2025-07-01",
            "data_fim_str": "2025-07-31",
            "supervisor_id": None,
            "condominio_id": None,
            "turno": None,
            "status": None
        }
        
        try:
            result_julho = get_ocorrencia_dashboard_data(filters_julho)
            print(f"   Total de ocorrências: {result_julho.get('total_ocorrencias', 'N/A')}")
            print(f"   Tipos encontrados: {len(result_julho.get('tipo_labels', []))}")
            print(f"   Condomínios encontrados: {len(result_julho.get('condominio_labels', []))}")
            
            print("   📊 Dados do gráfico de tipos:")
            tipo_labels = result_julho.get('tipo_labels', [])
            tipo_data = result_julho.get('ocorrencias_por_tipo_data', [])
            for i, (label, data) in enumerate(zip(tipo_labels, tipo_data)):
                print(f"      {i+1}. {label}: {data}")
                
        except Exception as e:
            print(f"   ❌ ERRO: {e}")
        
        # Teste 2: Com supervisor específico (ID 1 - Luis Royo)
        print("\n2️⃣ TESTE COM SUPERVISOR LUIS ROYO (ID 1):")
        filters_supervisor = {
            "data_inicio_str": "2025-07-01",
            "data_fim_str": "2025-07-31",
            "supervisor_id": 1,
            "condominio_id": None,
            "turno": None,
            "status": None
        }
        
        try:
            result_supervisor = get_ocorrencia_dashboard_data(filters_supervisor)
            print(f"   Total de ocorrências: {result_supervisor.get('total_ocorrencias', 'N/A')}")
            print(f"   Tipos encontrados: {len(result_supervisor.get('tipo_labels', []))}")
            
            print("   📊 Dados do gráfico de tipos (filtrado):")
            tipo_labels = result_supervisor.get('tipo_labels', [])
            tipo_data = result_supervisor.get('ocorrencias_por_tipo_data', [])
            for i, (label, data) in enumerate(zip(tipo_labels, tipo_data)):
                print(f"      {i+1}. {label}: {data}")
                
        except Exception as e:
            print(f"   ❌ ERRO: {e}")
            
    except Exception as e:
        print(f"❌ ERRO ao testar dashboard: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Função principal"""
    print("🚀 DEBUG COMPLETO DO BANCO DE DADOS")
    print("=" * 80)
    
    # Criar app Flask para contexto
    app = create_app()
    
    with app.app_context():
        # Verificar dados reais
        total_ocorrencias = verificar_dados_reais()
        
        # Verificar filtros simples
        verificar_filtros_simples(total_ocorrencias)
        
        # Testar dashboard com datas reais
        testar_dashboard_com_datas_reais()
        
        print("\n" + "=" * 80)
        print("💡 ANÁLISE:")
        print("   - Se não há dados nas tabelas, o problema é de dados")
        print("   - Se há dados nas tabelas mas não na view, o problema é na view")
        print("   - Se há dados na view mas os filtros não funcionam, o problema é na lógica")
        print("   - Verifique se o banco está sendo populado corretamente")


if __name__ == "__main__":
    main()
