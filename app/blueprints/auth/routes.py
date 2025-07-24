# app/blueprints/auth/routes.py

import jwt
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for, jsonify, session)
from flask_login import current_user, login_user, logout_user
from flask_cors import cross_origin

# --- CORREÇÃO: Importar 'limiter' junto com 'db' ---
from app import db, limiter, csrf
from app.forms import LoginForm, RegistrationForm
from app.models import LoginHistory, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Rota de registro de novo usuário."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            username = form.username.data or ""
            email = form.email.data or ""
            password = form.password.data or ""
            user = User(username=username, email=email)  # type: ignore
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(
                "Conta criada com sucesso. Aguarde aprovação do administrador.", "info"
            )
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro ao registrar usuário {form.username.data}: {e}"
            )
            flash("Erro ao criar a conta. Tente novamente.", "danger")
    return render_template("auth/register.html", title="Registrar", form=form)


# --- ADIÇÃO DO DECORATOR DE RATE LIMIT ---
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # Limita tentativas de login a 10 por minuto por IP
def login():
    """Rota de login de usuário."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        login_success = False

        if user and user.check_password(form.password.data):
            if not user.is_approved:
                flash("Conta ainda não aprovada.", "warning")
                _registrar_login(user, False, request, "Account not approved")
                return redirect(url_for("auth.login"))

            login_user(user, remember=form.remember.data)
            session.permanent = True  # Garante expiração por inatividade
            login_success = True
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()  # Garante que o last_login seja salvo imediatamente
            flash(f"Bem-vindo, {user.username}!", "success")
        else:
            flash("Login falhou. Verifique email e senha.", "danger")

        _registrar_login(
            user,
            login_success,
            request,
            None if login_success else "Credenciais inválidas",
        )

        if login_success:
            next_page = request.args.get("next")
            if not next_page or urlsplit(next_page).netloc != "":
                next_page = url_for("main.index")
            return redirect(next_page)

    return render_template("auth/login.html", title="Login", form=form)


# --- ROTA DE LOGIN PARA API ---
@auth_bp.route("/api/login", methods=["POST", "OPTIONS"])
@cross_origin()
@csrf.exempt
def api_login():
    if request.method == "OPTIONS":
        # O Flask-CORS normalmente responde automaticamente, mas garantimos status 200
        return '', 200
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"success": False, "message": "Email e senha são obrigatórios."}), 400
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        if not user.is_approved:
            return jsonify({"success": False, "message": "Conta ainda não aprovada."}), 403
        login_user(user)
        session.permanent = True  # Garante expiração por inatividade
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()  # Garante que o last_login seja salvo imediatamente
        # Registra o login no histórico
        _registrar_login(user, True, request, None)
        # Gera o token JWT
        payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=12)
        }
        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({
            "token": token,
            "message": f"Bem-vindo, {user.username}!",
            "success": True
        })
    return jsonify({"success": False, "message": "Credenciais inválidas."}), 401


@auth_bp.route("/logout")
def logout():
    """Rota de logout de usuário."""
    user_name = (
        current_user.username if current_user.is_authenticated else "Desconhecido"
    )
    logout_user()
    flash("Logout realizado com sucesso.", "info")
    current_app.logger.info(f"Usuário {user_name} deslogado.")
    return redirect(url_for("main.index"))


def _registrar_login(
    user: User | None, sucesso: bool, req, motivo_falha: str | None
) -> None:
    """Registra tentativa de login no histórico."""
    try:
        log = LoginHistory(  # type: ignore
            user_id=user.id if user else None,
            attempted_username=req.form.get("email"),
            timestamp=datetime.now(timezone.utc),
            success=sucesso,
            ip_address=req.remote_addr,
            user_agent=req.user_agent.string,
            failure_reason=motivo_falha,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar tentativa de login: {e}")
