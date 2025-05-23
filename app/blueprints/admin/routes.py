# app/blueprints/admin/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, LoginHistory, Ronda # Certifique-se de que Ronda é usado ou remova se não for.
from app.decorators.admin_required import admin_required # Verifique se este é o caminho correto
import logging

# Define o logger para este módulo
logger = logging.getLogger(__name__)

# Define o Blueprint com o prefixo URL
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/') # URL final será /admin/
@login_required
@admin_required
def dashboard():
    logger.info(f"Admin '{current_user.username}' acessou o painel /admin/. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
    return render_template('admin_dashboard.html', title='Painel Admin')

@admin_bp.route('/users') # URL final será /admin/users
@login_required
@admin_required
def manage_users():
    logger.info(f"Admin '{current_user.username}' acessou /admin/users. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
    page = request.args.get('page', 1, type=int)
    users_pagination_obj = User.query.order_by(User.date_registered.desc()).paginate(page=page, per_page=10)
    return render_template('admin_users.html', title='Gerenciar Usuários', users_pagination=users_pagination_obj)

@admin_bp.route('/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_approved:
        user.is_approved = True
        db.session.commit()
        flash(f'Usuário {user.username} aprovado com sucesso.', 'success')
        logger.info(f"Admin '{current_user.username}' aprovou o usuário '{user.username}' (ID: {user.id}).")
    else:
        flash(f'Usuário {user.username} já está aprovado.', 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/revoke', methods=['POST'])
@login_required
@admin_required
def revoke_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode revogar sua própria aprovação.', 'danger')
        logger.warning(f"Admin '{current_user.username}' tentou revogar a própria aprovação.")
        return redirect(url_for('admin.manage_users'))
    
    if user.is_approved:
        user.is_approved = False
        db.session.commit()
        flash(f'Aprovação de {user.username} foi revogada.', 'success')
        logger.info(f"Admin '{current_user.username}' revogou a aprovação do usuário '{user.username}' (ID: {user.id}).")
    else:
        flash(f'Aprovação do usuário {user.username} já estava revogada/pendente.', 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode alterar seu próprio status de administrador.', 'warning')
        logger.warning(f"Admin '{current_user.username}' tentou alterar o próprio status de admin.")
        return redirect(url_for('admin.manage_users'))

    user.is_admin = not user.is_admin
    if user.is_admin and not user.is_approved:
        user.is_approved = True
        flash(f'Usuário {user.username} também foi aprovado automaticamente ao se tornar admin.', 'info')
        logger.info(f"Usuário '{user.username}' (ID: {user.id}) aprovado automaticamente ao se tornar admin.")

    db.session.commit()
    status = "promovido a administrador" if user.is_admin else "rebaixado de administrador"
    flash(f'Usuário {user.username} foi {status} com sucesso.', 'success')
    logger.info(f"Admin '{current_user.username}' alterou o status de admin do usuário '{user.username}' (ID: {user.id}) para: {user.is_admin}.")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash('Você não pode deletar sua própria conta.', 'danger')
        logger.warning(f"Admin '{current_user.username}' tentou deletar a própria conta.")
        return redirect(url_for('admin.manage_users'))
    try:
        # Considerar synchronize_session='fetch' para consistência, se necessário.
        LoginHistory.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
        Ronda.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False) # Se Ronda tem user_id
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário {user_to_delete.username} deletado com sucesso.', 'success')
        logger.info(f"Admin '{current_user.username}' deletou o usuário '{user_to_delete.username}' (ID: {user_id}).")
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário {user_to_delete.username}: {str(e)}', 'danger')
        logger.error(f"Erro ao deletar usuário '{user_to_delete.username}' por admin '{current_user.username}': {e}", exc_info=True)
    return redirect(url_for('admin.manage_users'))

# NOVA ROTA PARA FERRAMENTAS ADMINISTRATIVAS
@admin_bp.route('/ferramentas') # URL final será /admin/ferramentas
@login_required
@admin_required
def admin_tools():
    # Esta linha usa logger, current_user e request.
    # Se o VSCode ainda reclamar, verifique as configurações do seu linter/Python interpreter.
    logger.info(f"Admin '{current_user.username}' acessou /admin/ferramentas. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
    return render_template('admin_ferramentas.html', title='Ferramentas Administrativas')
