from flask import (
    render_template, request, jsonify, redirect, url_for, flash,
    Blueprint, current_app
)
from app import db
from app.services.report_service import ReportService
from app.forms import RegistrationForm, LoginForm
from app.models import User, LoginHistory
from flask_login import login_user, current_user, logout_user, login_required
# from werkzeug.urls import url_parse # LINHA ANTIGA - REMOVER OU COMENTAR
from urllib.parse import urlsplit # NOVA IMPORTAÇÃO - da biblioteca padrão do Python
import logging
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

report_service_instance = None
try:
    report_service_instance = ReportService()
    logger.info("Instância de ReportService criada em routes.py (nível global do blueprint)")
except (ValueError, RuntimeError) as e:
    logger.critical(f"Falha na inicialização do ReportService em routes.py: {e}", exc_info=True)


@main_bp.route('/')
def index():
    current_app.logger.debug(f"Acessando rota / para IP: {request.remote_addr}")
    return render_template('index.html', title='Processador de Relatórios')

@main_bp.route('/register', methods=['GET', 'POST'])
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
            
            current_app.logger.info(f"Novo usuário registrado: {form.username.data} ({form.email.data})")
            flash(f'Conta criada com sucesso para {form.username.data}! Você já pode fazer login.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao registrar usuário {form.username.data}: {e}", exc_info=True)
            flash('Ocorreu um erro ao criar sua conta. Tente novamente.', 'danger')
    elif request.method == 'POST':
         current_app.logger.warning(f"Falha na validação do formulário de registro para o usuário: {form.username.data}, Erros: {form.errors}")

    return render_template('register.html', title='Registrar', form=form)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        login_success = False
        user_id_for_log = None

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            login_success = True
            user_id_for_log = user.id
            current_app.logger.info(f"Usuário {user.username} logado com sucesso. IP: {request.remote_addr}")
            flash(f'Login bem-sucedido, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            # CORREÇÃO AQUI 👇: Usando urlsplit para checagem de segurança do redirect
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            current_app.logger.warning(f"Tentativa de login falhou para o email: {form.email.data}. IP: {request.remote_addr}")
            flash('Login falhou. Verifique seu email e senha.', 'danger')
            if user:
                user_id_for_log = user.id
        
        try:
            log_entry = LoginHistory(
                user_id=user_id_for_log,
                attempted_username=form.email.data,
                timestamp=datetime.now(timezone.utc),
                success=login_success,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(log_entry)
            db.session.commit()
            current_app.logger.info(f"Registro de login para '{form.email.data}' (Sucesso: {login_success}) adicionado ao histórico.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao salvar o registro de login para '{form.email.data}': {e}", exc_info=True)
        
    elif request.method == 'POST':
        current_app.logger.warning(f"Falha na validação do formulário de login para o email: {form.email.data}, Erros: {form.errors}")

    return render_template('login.html', title='Login', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
         current_app.logger.info(f"Usuário {current_user.username} deslogado. IP: {request.remote_addr}")
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/processar_relatorio', methods=['POST'])
@login_required
def processar_relatorio_route():
    current_app.logger.info(f"Usuário {current_user.username} acessando /processar_relatorio. IP: {request.remote_addr}")

    if report_service_instance is None:
        current_app.logger.error(f"ReportService indisponível para {current_user.username}. IP: {request.remote_addr}")
        return jsonify({"erro": "Serviço de processamento indisponível."}), 503

    if not request.is_json:
        current_app.logger.warning(f"Requisição não JSON para /processar_relatorio por {current_user.username}. IP: {request.remote_addr}")
        return jsonify({"erro": "Requisição inválida: corpo deve ser JSON."}), 400

    data = request.get_json()
    if not data:
        current_app.logger.warning(f"Corpo JSON vazio em /processar_relatorio por {current_user.username}. IP: {request.remote_addr}")
        return jsonify({"erro": "Requisição inválida: corpo JSON vazio."}), 400

    relatorio_bruto = data.get('relatorio_bruto')