#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from app import db

def remove_views():
    """Remove as views problemáticas."""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("DROP VIEW IF EXISTS vw_colaboradores"))
                conn.execute(db.text("DROP VIEW IF EXISTS vw_logradouros"))
                conn.execute(db.text("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas"))
                conn.commit()
                print("✅ Views removidas com sucesso")
        except Exception as e:
            print(f"❌ Erro ao remover views: {str(e)}")

if __name__ == "__main__":
    remove_views() 