#!/usr/bin/env python3
"""
Script para corrigir a sequência da tabela escala_mensal
"""
import os
import sys
from sqlalchemy import text

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def fix_escala_mensal_sequence():
    """Corrige a sequência da tabela escala_mensal"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verifica o próximo valor da sequência
            result = db.session.execute(text("SELECT nextval('escala_mensal_id_seq')"))
            current_seq = result.scalar()
            
            # Verifica o maior ID na tabela
            result = db.session.execute(text("SELECT COALESCE(MAX(id), 0) FROM escala_mensal"))
            max_id = result.scalar()
            
            print(f"Sequência atual: {current_seq}")
            print(f"Maior ID na tabela: {max_id}")
            
            # Se a sequência está menor que o maior ID, corrige
            if current_seq <= max_id:
                new_seq = max_id + 1
                db.session.execute(text(f"SELECT setval('escala_mensal_id_seq', {new_seq})"))
                db.session.commit()
                print(f"Sequência corrigida para: {new_seq}")
            else:
                print("Sequência já está correta")
                
        except Exception as e:
            print(f"Erro ao corrigir sequência: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_escala_mensal_sequence()
