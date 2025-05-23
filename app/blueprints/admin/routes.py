from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, LoginHistory, Ronda
from app.decorators.admin_required import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin_dashboard.html', title='Painel Admin')

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.date_registered.desc()).paginate(page=page, per_page=10)
    return render_template('admin_users.html', title='Gerenciar Usuários', users_pagination=users)

@admin_bp.route('/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_approved:
        user.is_approved = True
        db.session.commit()
        flash(f'Usuário {user.username} aprovado com sucesso.', 'success')
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
        return redirect(url_for('admin.manage_users'))
    user.is_approved = False
    db.session.commit()
    flash(f'Aprovação de {user.username} foi revogada.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode alterar seu próprio status de administrador.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_admin = not user.is_admin
    if user.is_admin and not user.is_approved:
        user.is_approved = True
    db.session.commit()
    status = "promovido" if user.is_admin else "rebaixado"
    flash(f'Usuário {user.username} foi {status} com sucesso.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode deletar sua própria conta.', 'danger')
        return redirect(url_for('admin.manage_users'))
    try:
        LoginHistory.query.filter_by(user_id=user.id).delete()
        Ronda.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash(f'Usuário {user.username} deletado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário: {e}', 'danger')
    return redirect(url_for('admin.manage_users'))