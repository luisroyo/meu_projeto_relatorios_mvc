# app/decorators/admin_required.py
from functools import wraps
from flask import current_app, flash, redirect, url_for, request
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            current_app.logger.debug(f"Admin Required: Usuário não autenticado, redirecionando para login. Tentando acessar: {request.url}")
            return redirect(url_for('auth.login', next=request.url))

        # DEBUG: Adicionado para verificar o estado do current_user
        print(f"--- DEBUG @admin_required: Usuário: {current_user.username}, Email: {current_user.email}, is_admin: {current_user.is_admin}, is_approved: {current_user.is_approved} ---")
        # Você também pode usar o logger da aplicação se preferir, em vez de print:
        # current_app.logger.debug(f"@admin_required: Usuário: {current_user.username}, Email: {current_user.email}, is_admin: {current_user.is_admin}, is_approved: {current_user.is_approved}")

        if not current_user.is_admin:
            current_app.logger.warning(
                f"Usuário não admin ('{current_user.username if current_user.is_authenticated else 'N/A'}') "
                f"tentou acessar rota admin: {request.path}. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
            )
            flash('Acesso negado. Esta área é restrita a administradores.', 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function