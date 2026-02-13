#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from app import db

def clean_database():
    """Limpa tabelas temporárias do banco de dados."""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Remover tabelas temporárias do Alembic
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_colaborador"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_condominio"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_escala_mensal"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_gemini_usage_logs"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_login_history"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_ocorrencia"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_ocorrencia_orgaos"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_ocorrencia_tipo"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_orgao_publico"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_processing_history"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_ronda"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_ronda_esporadica"))
                conn.execute(db.text("DROP TABLE IF EXISTS _alembic_tmp_user"))
                
                # Remover views
                conn.execute(db.text("DROP VIEW IF EXISTS vw_colaboradores"))
                conn.execute(db.text("DROP VIEW IF EXISTS vw_logradouros"))
                conn.execute(db.text("DROP VIEW IF EXISTS vw_ocorrencias_detalhadas"))
                
                conn.commit()
                print("✅ Banco de dados limpo com sucesso")
        except Exception as e:
            print(f"❌ Erro ao limpar banco: {str(e)}")

if __name__ == "__main__":
    clean_database() 