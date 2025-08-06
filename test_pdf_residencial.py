#!/usr/bin/env python3
"""
Script de teste para verificar a funcionalidade de quantidades por residencial no PDF.
"""
from app import create_app, db
from app.services.dashboard.ronda_dashboard import get_ronda_dashboard_data
from app.services.report.ronda_service import RondaReportService
from datetime import datetime, timedelta
import os

def test_residencial_quantities_pdf():
    """Testa a geração do PDF com quantidades por residencial."""
    print("=== Testando PDF com Quantidades por Residencial ===")
    
    app = create_app()
    with app.app_context():
        try:
            # Define filtros para teste (últimos 30 dias)
            data_fim = datetime.now().date()
            data_inicio = data_fim - timedelta(days=30)
            
            filters = {
                "data_inicio_str": data_inicio.strftime("%Y-%m-%d"),
                "data_fim_str": data_fim.strftime("%Y-%m-%d"),
                "turno": "",
                "supervisor_id": None,
                "condominio_id": None,
                "mes": None,
                "data_especifica": ""
            }
            
            print(f"Filtros aplicados: {filters}")
            
            # Busca dados do dashboard
            print("Buscando dados do dashboard...")
            dashboard_data = get_ronda_dashboard_data(filters)
            
            # Verifica se temos dados de condomínios
            if dashboard_data.get('condominio_labels') and dashboard_data.get('condominio_data'):
                print(f"✅ Dados encontrados: {len(dashboard_data['condominio_labels'])} residenciais")
                
                # Mostra os dados encontrados
                print("\nDados dos Residenciais:")
                for i, (label, value) in enumerate(zip(dashboard_data['condominio_labels'], dashboard_data['condominio_data'])):
                    print(f"  {i+1}. {label}: {value} rondas")
                
                # Prepara informações dos filtros
                filters_info = {
                    "data_inicio": filters["data_inicio_str"],
                    "data_fim": filters["data_fim_str"],
                    "supervisor_name": None,
                    "condominio_name": None,
                    "turno": filters.get("turno", ""),
                    "mes": filters.get("mes")
                }
                
                # Gera PDF
                print("\nGerando PDF...")
                report_service = RondaReportService()
                pdf_buffer = report_service.generate_ronda_dashboard_pdf(dashboard_data, filters_info)
                
                # Salva o PDF para teste
                filename = f"teste_residencial_quantities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                with open(filename, 'wb') as f:
                    f.write(pdf_buffer.getvalue())
                
                print(f"✅ PDF gerado com sucesso: {filename}")
                print(f"📄 Tamanho do arquivo: {os.path.getsize(filename)} bytes")
                
                # Testa também o PDF compacto
                print("\nGerando PDF compacto...")
                pdf_compact_buffer = report_service.generate_compact_ronda_dashboard_pdf(dashboard_data, filters_info)
                
                filename_compact = f"teste_residencial_quantities_compact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                with open(filename_compact, 'wb') as f:
                    f.write(pdf_compact_buffer.getvalue())
                
                print(f"✅ PDF compacto gerado com sucesso: {filename_compact}")
                print(f"📄 Tamanho do arquivo compacto: {os.path.getsize(filename_compact)} bytes")
                
                return True
                
            else:
                print("❌ Nenhum dado de residencial encontrado para o período")
                print("Dados disponíveis no dashboard:")
                for key, value in dashboard_data.items():
                    if isinstance(value, (list, dict)) and value:
                        print(f"  - {key}: {len(value) if isinstance(value, list) else len(value.keys())} itens")
                    else:
                        print(f"  - {key}: {value}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_residencial_quantities_section():
    """Testa especificamente a seção de quantidades por residencial."""
    print("\n=== Testando Seção de Quantidades por Residencial ===")
    
    app = create_app()
    with app.app_context():
        try:
            # Dados de teste
            dashboard_data = {
                'condominio_labels': ['Residencial A', 'Residencial B', 'Residencial C', 'Residencial D'],
                'rondas_por_condominio_data': [15, 8, 0, 22]
            }
            
            periodo_inicio = "2025-01-01"
            periodo_fim = "2025-01-31"
            
            # Testa a seção
            report_service = RondaReportService()
            section_story = report_service._create_residencial_quantities_section(
                dashboard_data, periodo_inicio, periodo_fim
            )
            
            print(f"✅ Seção criada com sucesso: {len(section_story)} elementos")
            
            # Verifica se os elementos estão corretos
            for i, element in enumerate(section_story):
                print(f"  Elemento {i+1}: {type(element).__name__}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao testar seção: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("Iniciando testes de quantidades por residencial no PDF...")
    print("=" * 60)
    
    # Testa a seção específica
    section_success = test_residencial_quantities_section()
    
    # Testa a geração completa do PDF
    pdf_success = test_residencial_quantities_pdf()
    
    print("\n" + "=" * 60)
    print("Resumo dos testes:")
    print(f"Seção de Residenciais: {'✅ Sucesso' if section_success else '❌ Falha'}")
    print(f"Geração de PDF: {'✅ Sucesso' if pdf_success else '❌ Falha'}")
    
    if pdf_success:
        print("\n📋 Arquivos gerados:")
        for file in os.listdir('.'):
            if file.startswith('teste_residencial_quantities') and file.endswith('.pdf'):
                print(f"  - {file}")
    
    print("\n🎯 Verifique os arquivos PDF gerados para confirmar a funcionalidade!") 