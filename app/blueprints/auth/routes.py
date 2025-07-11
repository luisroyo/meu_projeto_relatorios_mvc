# app/blueprints/auth/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user
from datetime import datetime, timezone
from urllib.parse import urlsplit

# --- CORREÇÃO: Importar 'limiter' junto com 'db' ---
from app import db, limiter
from app.forms import RegistrationForm, LoginForm
from app.models import User, LoginHistory

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Conta criada com sucesso. Aguarde aprovação do administrador.', 'info')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao registrar usuário {form.username.data}: {e}")
            flash('Erro ao criar a conta. Tente novamente.', 'danger')
    return render_template('auth/register.html', title='Registrar', form=form)


# --- ADIÇÃO DO DECORATOR DE RATE LIMIT ---
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limita tentativas de login a 10 por minuto por IP
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        login_success = False

        if user and user.check_password(form.password.data):
            if not user.is_approved:
                flash('Conta ainda não aprovada.', 'warning')
                _registrar_login(user, False, request, 'Account not approved')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember.data)
            login_success = True
            user.last_login = datetime.now(timezone.utc)
            flash(f'Bem-vindo, {user.username}!', 'success')
        else:
            flash('Login falhou. Verifique email e senha.', 'danger')

        _registrar_login(user, login_success, request, None if login_success else 'Credenciais inválidas')

        if login_success:
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)

    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    user_name = current_user.username if current_user.is_authenticated else 'Desconhecido'
    logout_user()
    flash('Logout realizado com sucesso.', 'info')
    current_app.logger.info(f"Usuário {user_name} deslogado.")
    return redirect(url_for('main.index'))

def _registrar_login(user, sucesso, req, motivo_falha):
    try:
        log = LoginHistory(
            user_id=user.id if user else None,
            attempted_username=req.form.get('email'),
            timestamp=datetime.now(timezone.utc),
            success=sucesso,
            ip_address=req.remote_addr,
            user_agent=req.user_agent.string,
            failure_reason=motivo_falha
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar tentativa de login: {e}")