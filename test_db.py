#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from app.models.user import User
from app import db
from datetime import time, date

def test_database_structure():
    """Testa a estrutura do banco de dados."""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== Teste de Estrutura do Banco ===")
            
            # Verificar se a tabela existe
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='ronda_esporadica'"))
                table_exists = result.fetchone() is not None
                print(f"Tabela ronda_esporadica existe: {table_exists}")
                
                if not table_exists:
                    print("❌ Tabela ronda_esporadica não existe!")
                    return
                
                # Verificar estrutura da tabela
                result = conn.execute(db.text("PRAGMA table_info(ronda_esporadica)"))
                columns = result.fetchall()
                print(f"Colunas da tabela ronda_esporadica:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Verificar se há dados
                result = conn.execute(db.text("SELECT COUNT(*) FROM ronda_esporadica"))
                count = result.fetchone()[0]
                print(f"Total de registros na tabela: {count}")
            
            # Verificar condomínios
            condominios = Condominio.query.all()
            print(f"Total de condomínios: {len(condominios)}")
            
            # Verificar usuários
            users = User.query.all()
            print(f"Total de usuários: {len(users)}")
            
            print("=== Teste de Criação de Ronda ===")
            
            # Testar criação de uma ronda
            if condominios and users:
                condominio = condominios[0]
                user = users[0]
                
                print(f"Usando condomínio: {condominio.nome} (ID: {condominio.id})")
                print(f"Usando usuário: {user.username} (ID: {user.id})")
                
                # Criar ronda diretamente
                ronda = RondaEsporadica(
                    condominio_id=condominio.id,
                    user_id=user.id,
                    data_plantao=date.today(),
                    escala_plantao="06 às 18",
                    turno="Diurno",
                    hora_entrada=time(15, 30),
                    status="em_andamento"
                )
                
                print("Ronda criada em memória")
                
                # Adicionar à sessão
                db.session.add(ronda)
                print("Ronda adicionada à sessão")
                
                # Commit
                db.session.commit()
                print("Commit realizado com sucesso")
                
                # Verificar se foi salva
                ronda_salva = RondaEsporadica.query.get(ronda.id)
                if ronda_salva:
                    print(f"✅ Ronda salva com sucesso! ID: {ronda_salva.id}")
                    print(f"   Condomínio: {ronda_salva.condominio_id}")
                    print(f"   Usuário: {ronda_salva.user_id}")
                    print(f"   Status: {ronda_salva.status}")
                    
                    # Limpar
                    db.session.delete(ronda_salva)
                    db.session.commit()
                    print("Ronda de teste removida")
                else:
                    print("❌ Ronda não foi salva corretamente")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_database_structure() 