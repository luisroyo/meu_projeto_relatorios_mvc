#!/usr/bin/env python3
"""
Teste simples para verificar o problema com o modelo Ronda
"""

from app import create_app, db
from app.models.ronda import Ronda
from app.models.ronda_esporadica import RondaEsporadica
from datetime import datetime

def test_consulta_ronda():
    """Testa consulta simples no modelo Ronda"""
    app = create_app()
    with app.app_context():
        try:
            # Teste 1: Verificar se a tabela existe
            print("🧪 Testando consulta na tabela Ronda...")
            
            # Tentar buscar todas as rondas
            rondas = Ronda.query.all()
            print(f"✅ Total de rondas encontradas: {len(rondas)}")
            
            # Teste 2: Verificar campos disponíveis
            if rondas:
                primeira_ronda = rondas[0]
                print(f"✅ Primeira ronda ID: {primeira_ronda.id}")
                print(f"✅ Campo data_plantao_ronda: {primeira_ronda.data_plantao_ronda}")
                print(f"✅ Campo tipo: {primeira_ronda.tipo}")
            
            # Teste 3: Consulta específica
            print("\n🧪 Testando consulta específica...")
            ronda_esporadica = Ronda.query.filter_by(
                tipo="esporadica"
            ).first()
            
            if ronda_esporadica:
                print(f"✅ Ronda esporádica encontrada: ID {ronda_esporadica.id}")
            else:
                print("ℹ️ Nenhuma ronda esporádica encontrada")
            
            # Teste 4: Verificar modelo RondaEsporadica
            print("\n🧪 Testando modelo RondaEsporadica...")
            rondas_esporadicas = RondaEsporadica.query.all()
            print(f"✅ Total de rondas esporádicas: {len(rondas_esporadicas)}")
            
            if rondas_esporadicas:
                primeira_esporadica = rondas_esporadicas[0]
                print(f"✅ Primeira ronda esporádica ID: {primeira_esporadica.id}")
                print(f"✅ Campo data_plantao: {primeira_esporadica.data_plantao}")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_consulta_ronda() 