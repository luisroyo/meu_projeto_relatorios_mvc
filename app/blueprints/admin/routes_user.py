# app/blueprints/admin/routes_user.py
import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators.admin_required import admin_required
from app.models import User
from app.services.user_service import delete_user_and_dependencies

from . import admin_bp

logger = logging.getLogger(__name__)


# ... (rotas manage_users, approve_user, revoke_user, toggle_admin permanecem iguais) ...
@admin_bp.route("/users")
@login_required
@admin_required
def manage_users():
    logger.info(f"Admin '{current_user.username}' acessou /admin/users.")
    page = request.args.get("page", 1, type=int)
    users_pagination_obj = User.query.order_by(User.date_registered.desc()).paginate(
        page=page, per_page=10
    )
    return render_template(
        "admin/users.html",
        title="Gerenciar Usuários",
        users_pagination=users_pagination_obj,
    )


@admin_bp.route("/user/<int:user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_approved:
        user.is_approved = True
        db.session.commit()
        flash(f"Usuário {user.username} aprovado com sucesso.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/revoke", methods=["POST"])
@login_required
@admin_required
def revoke_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        if user.is_approved:
            user.is_approved = False
            db.session.commit()
            flash(f"Aprovação de {user.username} foi revogada.", "success")
    else:
        flash("Você não pode revogar sua própria aprovação.", "danger")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/toggle_admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        user.is_admin = not user.is_admin
        if user.is_admin and not user.is_approved:
            user.is_approved = True
            flash(
                f"Usuário {user.username} também foi aprovado automaticamente.", "info"
            )
        db.session.commit()
        status = (
            "promovido a administrador"
            if user.is_admin
            else "rebaixado de administrador"
        )
        flash(f"Usuário {user.username} foi {status} com sucesso.", "success")
    else:
        flash("Você não pode alterar seu próprio status de administrador.", "warning")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/toggle_supervisor", methods=["POST"])
@login_required
@admin_required
def toggle_supervisor(user_id):
    user = User.query.get_or_404(user_id)

    ## [CORREÇÃO] Adicionada verificação para impedir que o usuário altere o próprio status.
    # Isso torna a função consistente com toggle_admin e revoke_user.
    if user.id == current_user.id:
        flash("Você não pode alterar seu próprio status de supervisor.", "warning")
        return redirect(url_for("admin.manage_users"))

    user.is_supervisor = not user.is_supervisor
    if user.is_supervisor and not user.is_approved:
        user.is_approved = True
        flash(f"Usuário {user.username} também foi aprovado automaticamente.", "info")
    db.session.commit()
    status = (
        "promovido a supervisor" if user.is_supervisor else "rebaixado de supervisor"
    )
    flash(f"Usuário {user.username} foi {status} com sucesso.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("Você não pode deletar sua própria conta.", "danger")
        return redirect(url_for("admin.manage_users"))

    # Chama o serviço para realizar a exclusão
    sucesso, mensagem = delete_user_and_dependencies(user_id)

    if sucesso:
        flash(mensagem, "success")
    else:
        logger.error(f"Falha ao deletar usuário ID {user_id}: {mensagem}")
        flash(mensagem, "danger")

    return redirect(url_for("admin.manage_users"))
