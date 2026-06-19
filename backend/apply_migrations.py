#!/usr/bin/env python3
"""
Script para aplicar migrações do banco de dados
"""
from app import create_app
from config import DevelopmentConfig
from app import db

def apply_migrations():
    """Aplica as migrações do banco de dados"""
    print("Iniciando aplicação de migrações...")
    
    # Cria a aplicação
    app = create_app(DevelopmentConfig)
    
    with app.app_context():
        print("Conectando ao banco de dados...")
        try:
            # Cria todas as tabelas (incluindo os novos campos)
            db.create_all()
            print("[OK] Tabelas criadas/atualizadas com sucesso!")
            
            # Verifica se os novos campos foram criados
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Verifica tabela parada
            tables = inspector.get_table_names()
            if 'parada' in tables:
                print("[OK] Tabela 'parada' criada/verificada com sucesso!")
            else:
                print("[ERRO] Tabela 'parada' nao encontrada!")
                
            columns = inspector.get_columns('ronda')
            
            new_fields = ['km_entrada', 'km_saida', 'km_total_percorrido', 'data_hora_entrada', 'data_hora_saida']
            existing_fields = [col['name'] for col in columns]
            
            print(f"Campos existentes na tabela ronda: {existing_fields}")
            
            for field in new_fields:
                if field in existing_fields:
                    print(f"[OK] Campo {field} encontrado!")
                else:
                    print(f"[AVISO] Campo {field} NAO encontrado!")
                    
        except Exception as e:
            print(f"[ERRO] Erro ao aplicar migracoes: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = apply_migrations()
    if success:
        print("Migracoes aplicadas com sucesso!")
    else:
        print("Falha ao aplicar migracoes!")
