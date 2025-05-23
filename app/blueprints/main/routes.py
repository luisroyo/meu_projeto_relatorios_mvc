# app/blueprints/main/routes.py
from flask import Blueprint, render_template, current_app, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user # Adicionado current_user se for usar para logs
from app import db
from app.models import User
import os
import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__) # Define um logger para este módulo

@main_bp.route('/')
@login_required
def index():
    # Adicionando log similar ao que estava no seu routesOld.py
    logger.debug(
        f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} "
        f"({current_user.username if current_user.is_authenticated else 'N/A'}). "
        f"IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
    )
    return render_template('index.html', title='Analisador de Relatórios IA')

# app/blueprints/main/routes.py
# ... (importações e definições de blueprint/logger) ...

# ROTA TEMPORÁRIA PARA CRIAR/VERIFICAR O USUÁRIO ADMINISTRADOR
# LEMBRE-SE DE REMOVER ESTA ROTA APÓS O USO!
@main_bp.route('/_create-super-admin-user-temp/<string:secret_token>', methods=['GET'])
def create_initial_admin_user(secret_token):
    configured_token = os.getenv('ADMIN_SETUP_TOKEN')
    if not configured_token or secret_token != configured_token:
        logger.warning(f"Tentativa de acesso não autorizado ao setup de admin. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
        return "Acesso não autorizado.", 403

    admin_email = 'luisroyo25@gmail.com'
    admin_username = 'Luis Royo' # ou o username que preferir
    admin_password = 'edu123cs' # Sua senha

    user = User.query.filter_by(email=admin_email).first()

    if user:
        if user.is_admin:
            logger.info(f"Usuário administrador '{user.username}' com email '{admin_email}' já existe e é admin.")
            flash(f"Usuário administrador '{user.username}' já existe e está configurado corretamente. Faça login.", "info")
        else: # Usuário existe mas não é admin
            user.is_admin = True
            user.is_approved = True # Garante que está aprovado
            # Você pode decidir se quer resetar a senha aqui ou não
            # user.set_password(admin_password)
            try:
                db.session.commit()
                logger.info(f"Usuário existente '{user.username}' promovido a administrador.")
                flash(f"Usuário existente '{user.username}' promovido a administrador. Faça login.", "success")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro ao promover usuário existente '{user.username}' a administrador: {e}", exc_info=True)
                return f"Erro ao promover usuário '{user.username}': {str(e)}", 500
    else: # Usuário não existe, vamos criar
        try:
            new_admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True,
                is_approved=True
            )
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            db.session.commit()
            logger.info(f"Novo usuário administrador '{admin_username}' (Email: {admin_email}) criado com sucesso!")
            flash(f"Novo usuário administrador '{admin_username}' criado com sucesso! Faça login.", "success")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar novo usuário administrador: {e}", exc_info=True)
            return f"Erro ao criar novo usuário administrador: {str(e)}", 500

    return redirect(url_for('auth.login'))