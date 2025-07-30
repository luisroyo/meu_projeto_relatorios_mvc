#!/usr/bin/env python3
"""
Script para criar dados de teste para rondas esporádicas
"""

from app import create_app, db
from app.models.condominio import Condominio
from app.models.user import User
from app.models.ronda_esporadica import RondaEsporadica
from datetime import datetime, time, date

def criar_dados_teste():
    """Cria dados de teste necessários"""
    app = create_app()
    with app.app_context():
        try:
            # 1. Criar condomínio de teste
            condominio = Condominio.query.filter_by(id=1).first()
            if not condominio:
                condominio = Condominio(
                    id=1,
                    nome="Residencial Teste"
                )
                db.session.add(condominio)
                print("✅ Condomínio criado")

            # 2. Criar usuários de teste
            user1 = User.query.filter_by(id=1).first()
            if not user1:
                user1 = User(
                    id=1,
                    username="usuario_teste",
                    email="usuario@teste.com",
                    password_hash="teste123"
                )
                db.session.add(user1)
                print("✅ Usuário 1 criado")

            user2 = User.query.filter_by(id=2).first()
            if not user2:
                user2 = User(
                    id=2,
                    username="supervisor_teste",
                    email="supervisor@teste.com",
                    password_hash="teste123"
                )
                db.session.add(user2)
                print("✅ Usuário 2 (supervisor) criado")

            # 3. Commit das alterações
            db.session.commit()
            print("✅ Dados de teste criados com sucesso!")

            # 4. Criar algumas rondas esporádicas de teste
            data_teste = date(2025, 1, 30)
            
            # Ronda 1
            ronda1 = RondaEsporadica(
                condominio_id=1,
                user_id=1,
                supervisor_id=2,
                data_plantao=data_teste,
                escala_plantao="06h às 18h",
                turno="Diurno",
                hora_entrada=time(8, 0),  # 08:00
                hora_saida=time(10, 30),  # 10:30
                observacoes="Primeira ronda do dia",
                status="finalizada",
                duracao_minutos=150
            )
            db.session.add(ronda1)

            # Ronda 2
            ronda2 = RondaEsporadica(
                condominio_id=1,
                user_id=1,
                supervisor_id=2,
                data_plantao=data_teste,
                escala_plantao="06h às 18h",
                turno="Diurno",
                hora_entrada=time(14, 0),  # 14:00
                hora_saida=time(16, 0),    # 16:00
                observacoes="Segunda ronda do dia",
                status="finalizada",
                duracao_minutos=120
            )
            db.session.add(ronda2)

            # Ronda 3 (em andamento)
            ronda3 = RondaEsporadica(
                condominio_id=1,
                user_id=1,
                supervisor_id=2,
                data_plantao=data_teste,
                escala_plantao="06h às 18h",
                turno="Diurno",
                hora_entrada=time(17, 0),  # 17:00
                hora_saida=None,
                observacoes="Ronda em andamento",
                status="em_andamento",
                duracao_minutos=0
            )
            db.session.add(ronda3)

            db.session.commit()
            print("✅ Rondas esporádicas de teste criadas!")

            print("\n📊 Resumo dos dados criados:")
            print(f"   - Condomínio: {condominio.nome}")
            print(f"   - Usuários: {user1.username}, {user2.username}")
            print(f"   - Rondas esporádicas: 3 criadas")
            print(f"   - Data de teste: {data_teste}")

        except Exception as e:
            print(f"❌ Erro ao criar dados de teste: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    criar_dados_teste() 