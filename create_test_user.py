#!/usr/bin/env python3
"""
Script para criar um usuário de teste para debug do JWT.
"""
from app import create_app, db
from app.models.user import User

def create_test_user():
    app = create_app()
    with app.app_context():
        # Verificar se o usuário já existe
        user = User.query.filter_by(email='test@test.com').first()
        
        if not user:
            # Criar novo usuário de teste
            user = User(
                username='Test User',
                email='test@test.com',
                is_approved=True,
                is_admin=False,
                is_supervisor=False
            )
            user.set_password('123456')
            
            db.session.add(user)
            db.session.commit()
            print("✅ Usuário de teste criado com sucesso!")
            print(f"   Email: test@test.com")
            print(f"   Senha: 123456")
        else:
            print("ℹ️  Usuário de teste já existe")
            print(f"   Email: {user.email}")
            print(f"   Senha: 123456")
        
        # Verificar se a senha está correta
        if user.check_password('123456'):
            print("✅ Senha verificada com sucesso!")
        else:
            print("❌ Erro na verificação da senha!")

if __name__ == '__main__':
    create_test_user() 