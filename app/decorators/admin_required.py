# app/decorators/admin_required.py (ou app/utils/decorators.py)
from functools import wraps
from flask import current_app, flash, redirect, url_for, request
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Ajuste para o nome do seu blueprint de autenticação e rota de login
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            current_app.logger.warning(
                f"Usuário não admin ({current_user.username if current_user.is_authenticated else 'N/A'}) "
                f"tentou acessar rota admin: {request.path}. IP: {request.remote_addr}"
            )
            flash('Acesso negado. Esta área é restrita a administradores.', 'danger')
            # Ajuste para o nome do seu blueprint principal e rota de índice
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function