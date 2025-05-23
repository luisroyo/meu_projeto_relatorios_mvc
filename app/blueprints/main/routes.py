# app/blueprints/main/routes.py
from flask import Blueprint, render_template, current_app, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user # Adicionado current_user
from app import db
from app.models import User # Certifique-se que este é o caminho correto para seu modelo User
import os
import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main_bp.route('/')
@login_required
def index():
    logger.debug(
        f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} "
        f"({current_user.username if current_user.is_authenticated else 'N/A'}). "
        f"IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
    )
    return render_template('index.html', title='Analisador de Relatórios IA')

# ROTA TEMPORÁRIA PARA CRIAR/VERIFICAR O USUÁRIO ADMINISTRADOR
# LEMBRE-SE DE REMOVER ESTA ROTA DO CÓDIGO APÓS O USO!
@main_bp.route('/_create-super-admin-user-temp/<string:secret_token>', methods=['GET'])
def create_initial_admin_user(secret_token):
    # 1. Obtenha o token secreto configurado nas variáveis de ambiente
    configured_token = os.getenv('ADMIN_SETUP_TOKEN')

    # 2. Verifique se o token da URL corresponde ao token configurado
    if not configured_token or secret_token != configured_token:
        logger.warning(
            f"Tentativa de acesso não autorizado ao setup de admin. Token da URL: '{secret_token}'. "
            f"IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
        )
        return "Acesso não autorizado. Token inválido ou não configurado.", 403

    # 3. Dados do administrador que você quer criar/garantir
    admin_email = 'luisroyo25@gmail.com'
    admin_username = 'Luis Royo' # ou o username que você definiu
    admin_password = 'edu123cs'  # a senha que você definiu

    try:
        # 4. Procure pelo usuário com o email fornecido
        user = User.query.filter_by(email=admin_email).first()

        if user:
            # Usuário com este email já existe. Vamos garantir que ele seja admin e aprovado.
            logger.info(f"Usuário com email '{admin_email}' (username: '{user.username}') já existe. Verificando status...")
            needs_commit = False
            if not user.is_admin:
                user.is_admin = True
                logger.info(f"Usuário '{user.username}' promovido a administrador.")
                needs_commit = True
            if not user.is_approved:
                user.is_approved = True
                logger.info(f"Usuário '{user.username}' agora está aprovado.")
                needs_commit = True
            
            # Opcional: Se quiser garantir que a senha seja a definida acima, descomente a linha abaixo.
            # Cuidado: Isso mudará a senha do usuário existente se ela for diferente.
            # user.set_password(admin_password)
            # logger.info(f"Senha do usuário '{user.username}' verificada/redefinida (se descomentado).")
            # needs_commit = True # Se descomentar set_password, precisa de commit

            if needs_commit:
                db.session.commit()
                flash(f"Usuário administrador '{user.username}' atualizado e aprovado. Faça login.", "success")
            else:
                flash(f"Usuário administrador '{user.username}' já está configurado e aprovado. Faça login.", "info")
            
        else:
            # Usuário com este email não existe, então vamos criar um novo.
            # Antes, verifica se já existe *algum* outro admin (para evitar criar múltiplos admins por este método acidentalmente)
            # Se você quiser que esta rota SEMPRE crie/atualize o SEU admin, pode remover esta checagem de 'existing_admin_any'
            # ou ajustá-la para permitir a criação do SEU admin específico.
            existing_admin_any = User.query.filter(User.email != admin_email, User.is_admin == True).first()
            if existing_admin_any:
                logger.warning(
                    f"Tentativa de criar novo admin '{admin_email}', mas outro administrador ('{existing_admin_any.username}') já existe. "
                    f"Para criar/atualizar '{admin_email}', ele não pode existir ou precisa ser o único admin a ser criado por este script."
                )
                flash(f"Outro administrador ('{existing_admin_any.username}') já existe. O usuário '{admin_email}' não foi criado. Verifique o banco de dados.", "warning")
                return redirect(url_for('auth.login'))

            logger.info(f"Criando novo usuário administrador: Email='{admin_email}', Username='{admin_username}'")
            new_admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True,
                is_approved=True  # Define como admin e aprovado na criação
            )
            new_admin.set_password(admin_password)
            
            db.session.add(new_admin)
            db.session.commit()
            
            logger.info(f"Novo usuário administrador '{admin_username}' (Email: {admin_email}) criado com sucesso e aprovado!")
            flash(f"Novo usuário administrador '{admin_username}' criado com sucesso! Faça login.", "success")

        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro crítico durante o setup do administrador para '{admin_email}': {e}", exc_info=True)
        # Não use flash aqui, pois o redirect pode não funcionar se o erro for grave
        return f"Erro crítico ao tentar configurar o usuário administrador: {str(e)}. Verifique os logs.", 500