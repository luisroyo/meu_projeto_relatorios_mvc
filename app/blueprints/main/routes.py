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

# ROTA TEMPORÁRIA PARA CRIAR O USUÁRIO ADMINISTRADOR
# LEMBRE-SE DE REMOVER ESTA ROTA APÓS O USO!
@main_bp.route('/_create-super-admin-user-temp/<string:secret_token>', methods=['GET'])
def create_initial_admin_user(secret_token):
    # 1. Obtenha o token secreto configurado nas variáveis de ambiente
    configured_token = os.getenv('ADMIN_SETUP_TOKEN')

    # 2. Verifique se o token da URL corresponde ao token configurado
    if not configured_token or secret_token != configured_token:
        logger.warning(
            f"Tentativa de acesso não autorizado ao setup de admin. "
            f"IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
        )
        return "Acesso não autorizado.", 403

    # 3. Defina os dados do administrador com base nos dados fornecidos
    admin_email = 'luisroyo25@gmail.com'
    admin_username = 'Luis Royo'  # Ou um username mais curto se preferir, ex: 'luisroyo'
    admin_password = 'edu123cs'

    # 4. Verifique se um administrador ou usuário com este email já existe
    # Primeiro, verifica se já existe algum admin (para evitar múltiplos admins por este método)
    existing_admin_any = User.query.filter_by(is_admin=True).first()
    if existing_admin_any:
        logger.info(
            f"Um usuário administrador ('{existing_admin_any.username}') já existe. "
            f"Nenhuma ação adicional tomada por este endpoint."
        )
        flash(f"Um usuário administrador ('{existing_admin_any.username}') já existe. Login não foi realizado automaticamente.", "info")
        return redirect(url_for('auth.login'))


    # Depois, verifica se o email específico já está em uso
    user_with_email_exists = User.query.filter_by(email=admin_email).first()
    if user_with_email_exists:
        logger.warning(
            f"Tentativa de criar admin, mas o email '{admin_email}' já está em uso por "
            f"'{user_with_email_exists.username}'. Promovendo a admin se não for."
        )
        # Se o usuário com este email existe mas não é admin, promove-o
        if not user_with_email_exists.is_admin:
            user_with_email_exists.is_admin = True
            user_with_email_exists.is_approved = True # Garante aprovação
            # Considerar se a senha deve ser resetada aqui ou não. Por segurança, não vamos resetar.
            # Se precisar resetar: user_with_email_exists.set_password(admin_password)
            try:
                db.session.commit()
                logger.info(f"Usuário existente '{user_with_email_exists.username}' promovido a administrador.")
                flash(f"Usuário existente '{user_with_email_exists.username}' promovido a administrador. Faça login.", "success")
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro ao promover usuário existente a administrador: {e}", exc_info=True)
                return f"Erro ao promover usuário existente a administrador: {str(e)}", 500
        else:
            # O usuário com este email já é admin, o que contradiz a checagem anterior de existing_admin_any
            # Isso pode acontecer se o primeiro admin foi criado com outro email.
             flash(f"O usuário com email '{admin_email}' já é um administrador. Login não foi realizado automaticamente.", "info")
             return redirect(url_for('auth.login'))


    # 5. Crie o novo usuário administrador (só chega aqui se não houver admin e o email não estiver em uso)
    try:
        new_admin = User(
            username=admin_username,
            email=admin_email,
            is_admin=True,
            is_approved=True  # Aprova automaticamente o admin
        )
        new_admin.set_password(admin_password) # Use o método do seu modelo para definir a senha (hash)
        
        db.session.add(new_admin)
        db.session.commit()
        
        logger.info(f"Usuário administrador '{admin_username}' (Email: {admin_email}) criado com sucesso!")
        flash(f"Usuário administrador '{admin_username}' criado com sucesso! Faça login com as credenciais definidas.", "success")
        return redirect(url_for('auth.login')) 
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário administrador: {e}", exc_info=True)
        return f"Erro ao criar usuário administrador: {str(e)}", 500
