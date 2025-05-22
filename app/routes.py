from flask import (
    render_template, request, jsonify, redirect, url_for, flash,
    Blueprint, current_app, abort
)
from app import db
from app.services.report_service import ReportService
# Certifique-se que o import abaixo reflete sua estrutura após a refatoração do rondaservice
# Se processar_log_de_rondas está agora em app.services.ronda_logic.processor, ajuste o import.
# Exemplo: from app.services.ronda_logic.processor import processar_log_de_rondas
from app.services.rondaservice import processar_log_de_rondas 
from app.forms import RegistrationForm, LoginForm, TestarRondasForm
from app.models import User, LoginHistory, Ronda # Certifique-se que Ronda está importado
from flask_login import login_user, current_user, logout_user, login_required
from urllib.parse import urlsplit
import logging
from datetime import datetime, timezone
from functools import wraps

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__) # Logger específico para este módulo

report_service_instance = None
try:
    report_service_instance = ReportService()
    logger.info("Instância de ReportService criada em routes.py (nível global do blueprint)")
except (ValueError, RuntimeError) as e:
    logger.critical(f"Falha na inicialização do ReportService em routes.py: {e}", exc_info=True)

# --- DECORADOR ADMIN_REQUIRED ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.url))
        if not current_user.is_admin:
            current_app.logger.warning(f"Usuário não admin ({current_user.username}) tentou acessar uma rota protegida. IP: {request.remote_addr}")
            flash('Acesso negado. Esta área é restrita a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS PRINCIPAIS E DE AUTENTICAÇÃO ---
@main_bp.route('/')
@login_required
def index():
    current_app.logger.debug(f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} ({current_user.username})")
    return render_template('index.html', title='Analisador de Relatórios IA')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        current_app.logger.info(f"Usuário já autenticado ({current_user.username}) tentou acessar /register. Redirecionando para index.")
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data) 
            # is_approved e is_admin já têm default=False no modelo User
            
            db.session.add(user)
            db.session.commit()
            
            current_app.logger.info(f"Novo usuário registrado: {form.username.data} ({form.email.data}). Aguardando aprovação.")
            flash('Sua conta foi criada com sucesso e agora aguarda aprovação do administrador para acesso completo.', 'info')
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
        current_app.logger.info(f"Usuário já autenticado ({current_user.username}) tentou acessar /login. Redirecionando para index.")
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        login_success = False
        user_id_for_log = user.id if user else None

        current_app.logger.debug(f"Tentativa de login para email: {form.email.data}. Usuário encontrado: {'Sim' if user else 'Não'}")

        if user and user.check_password(form.password.data):
            current_app.logger.info(f"Verificação de senha para {user.username} bem-sucedida.")
            
            if not user.is_approved:
                current_app.logger.warning(f"Tentativa de login por usuário não aprovado: {user.username} ({user.email}). IP: {request.remote_addr}")
                flash('Sua conta ainda não foi aprovada por um administrador. Tente novamente mais tarde.', 'warning')
                try:
                    log_entry_unapproved = LoginHistory(
                        user_id=user.id,
                        attempted_username=form.email.data,
                        timestamp=datetime.now(timezone.utc),
                        success=False,
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string,
                        failure_reason='Account not approved' # Adicione este campo ao modelo LoginHistory e migre
                    )
                    db.session.add(log_entry_unapproved)
                    db.session.commit()
                except Exception as e_log:
                    db.session.rollback()
                    current_app.logger.error(f"Erro ao salvar o registro de login (não aprovado) para '{form.email.data}': {e_log}", exc_info=True)
                return redirect(url_for('main.login'))

            login_user(user, remember=form.remember.data) # Verifique se 'form.remember.data' é o campo correto no seu LoginForm
            login_success = True
            user.last_login = datetime.now(timezone.utc)
            
            current_app.logger.info(f"Usuário {user.username} autenticado com sucesso: {current_user.is_authenticated}. Aprovado: {user.is_approved}")
            flash(f'Login bem-sucedido, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            current_app.logger.debug(f"Parâmetro next_page do login: {next_page}")
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.index')
            current_app.logger.info(f"Redirecionando usuário {user.username} para: {next_page} após login.")
        else:
            if user: 
                current_app.logger.warning(f"Tentativa de login falhou para o usuário {user.username} (email: {form.email.data}). Senha incorreta. IP: {request.remote_addr}")
            else: 
                current_app.logger.warning(f"Tentativa de login falhou. Email não encontrado: {form.email.data}. IP: {request.remote_addr}")
            flash('Login falhou. Verifique seu email e senha.', 'danger')
        
        # Registra no LoginHistory e commita last_login se sucesso
        if not (user and user.check_password(form.password.data) and not user.is_approved): # Evita logar de novo se já logou falha de aprovação
            try:
                log_entry = LoginHistory(
                    user_id=user_id_for_log,
                    attempted_username=form.email.data,
                    timestamp=datetime.now(timezone.utc),
                    success=login_success,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    failure_reason=None if login_success else ('Incorrect password' if user else 'Email not found') # Adicione este campo ao modelo LoginHistory e migre
                )
                db.session.add(log_entry)
                # user.last_login já foi definido se login_success é True
                db.session.commit() # Commit para LoginHistory e user.last_login (se sucesso)
                if login_success and user:
                     current_app.logger.info(f"Último login de {user.username} e registro de LoginHistory commitados.")
                current_app.logger.info(f"Registro de login para '{form.email.data}' (Sucesso: {login_success}) adicionado ao histórico.")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro ao salvar o registro de login e/ou last_login para '{form.email.data}': {e}", exc_info=True)
        
        if login_success:
             return redirect(next_page)
        # else: # Se falhou (senha incorreta, email não encontrado), renderiza o form de login novamente
            # return render_template('login.html', title='Login', form=form) # Já é o retorno padrão no final

    elif request.method == 'POST': 
        current_app.logger.warning(f"Falha na validação do formulário de login (validate_on_submit falhou). Email tentado: {form.email.data}, Erros: {form.errors}")
    return render_template('login.html', title='Login', form=form)

@main_bp.route('/logout')
@login_required 
def logout():
    user_name_before_logout = current_user.username if current_user.is_authenticated else "Usuário Desconhecido"
    logout_user() 
    flash('Você foi desconectado com sucesso.', 'info')
    current_app.logger.info(f"Usuário {user_name_before_logout} deslogado. IP: {request.remote_addr}")
    return redirect(url_for('main.index'))

# --- ROTAS DE ADMINISTRAÇÃO ---
@main_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', title='Painel Admin')

@main_bp.route('/admin/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.order_by(User.date_registered.desc()).paginate(page=page, per_page=10)
    current_app.logger.info(f"Admin {current_user.username} acessou /admin/users. Página: {page}")
    return render_template('admin_users.html', title='Gerenciar Usuários', users_pagination=users_pagination)

@main_bp.route('/admin/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user_to_approve = User.query.get_or_404(user_id)
    if user_to_approve.is_approved:
        flash(f'Usuário {user_to_approve.username} já está aprovado.', 'info')
    else:
        user_to_approve.is_approved = True
        db.session.commit()
        flash(f'Usuário {user_to_approve.username} aprovado com sucesso.', 'success')
        current_app.logger.info(f"Admin {current_user.username} aprovou o usuário {user_to_approve.username} (ID: {user_id}).")
    return redirect(url_for('main.manage_users'))

@main_bp.route('/admin/user/<int:user_id>/revoke', methods=['POST'])
@login_required
@admin_required
def revoke_user_approval(user_id):
    user_to_revoke = User.query.get_or_404(user_id)
    if user_to_revoke.id == current_user.id:
        flash('Você não pode revogar sua própria aprovação.', 'danger')
        current_app.logger.warning(f"Admin {current_user.username} tentou revogar a própria aprovação.")
        return redirect(url_for('main.manage_users'))
        
    if not user_to_revoke.is_approved: # Se já não estiver aprovado (pendente)
        flash(f'Aprovação do usuário {user_to_revoke.username} já está revogada/pendente.', 'info')
    else:
        user_to_revoke.is_approved = False
        db.session.commit()
        flash(f'Aprovação do usuário {user_to_revoke.username} foi revogada.', 'success')
        current_app.logger.info(f"Admin {current_user.username} revogou a aprovação do usuário {user_to_revoke.username} (ID: {user_id}).")
    return redirect(url_for('main.manage_users'))

@main_bp.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin_status(user_id):
    user_to_toggle = User.query.get_or_404(user_id)
    
    if user_to_toggle.id == current_user.id:
        flash('Você não pode alterar seu próprio status de administrador desta forma.', 'warning')
        current_app.logger.warning(f"Admin {current_user.username} tentou alterar o próprio status de admin via toggle.")
        return redirect(url_for('main.manage_users'))

    user_to_toggle.is_admin = not user_to_toggle.is_admin
    if user_to_toggle.is_admin and not user_to_toggle.is_approved:
        user_to_toggle.is_approved = True
        flash(f'Usuário {user_to_toggle.username} também foi aprovado automaticamente ao se tornar admin.', 'info')

    db.session.commit()
    status_message = "promovido a administrador" if user_to_toggle.is_admin else "rebaixado de administrador"
    flash(f'Usuário {user_to_toggle.username} foi {status_message}.', 'success')
    current_app.logger.info(f"Admin {current_user.username} alterou o status de admin do usuário {user_to_toggle.username} (ID: {user_id}) para: {user_to_toggle.is_admin}.")
    return redirect(url_for('main.manage_users'))

@main_bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.id == current_user.id:
        flash('Você não pode deletar sua própria conta de administrador.', 'danger')
        current_app.logger.warning(f"Admin {current_user.username} tentou deletar a própria conta.")
        return redirect(url_for('main.manage_users'))

    try:
        # Deletar registros relacionados explicitamente
        # Assumindo que 'login_history_entries' é o backref em User para LoginHistory
        # e 'rondas' é o relacionamento em User para Ronda.
        # Verifique os nomes exatos dos seus relacionamentos/backrefs nos modelos.
        
        # Deleta LoginHistory associado
        LoginHistory.query.filter_by(user_id=user_to_delete.id).delete()
        
        # Deleta Rondas associadas
        Ronda.query.filter_by(user_id=user_to_delete.id).delete()
        
        # Agora deleta o usuário
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário {user_to_delete.username} (ID: {user_id}) e seus dados relacionados foram deletados com sucesso.', 'success')
        current_app.logger.info(f"Admin {current_user.username} deletou o usuário {user_to_delete.username} (ID: {user_id}).")
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar o usuário {user_to_delete.username}: {str(e)}', 'danger')
        current_app.logger.error(f"Erro ao deletar usuário {user_to_delete.username} (ID: {user_id}) por admin {current_user.username}: {e}", exc_info=True)
        
    return redirect(url_for('main.manage_users'))

# --- SUAS ROTAS DE SERVIÇO ---
@main_bp.route('/processar_relatorio', methods=['POST'])
@login_required 
def processar_relatorio_route():
    current_app.logger.info(f"Iniciando /processar_relatorio. Autenticado: {current_user.is_authenticated}, Usuário: {current_user.username if current_user.is_authenticated else 'N/A'}. IP: {request.remote_addr}")
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

    if relatorio_bruto is None:
        current_app.logger.warning(f"Campo 'relatorio_bruto' não encontrado por {current_user.username}. IP: {request.remote_addr}")
        return jsonify({"erro": "Campo 'relatorio_bruto' não encontrado."}), 400
    if not isinstance(relatorio_bruto, str):
        current_app.logger.warning(f"'relatorio_bruto' não é string por {current_user.username}. IP: {request.remote_addr}")
        return jsonify({"erro": "'relatorio_bruto' deve ser uma string."}), 400
    
    MAX_INPUT_LENGTH_SERVER = 12000 
    if not relatorio_bruto.strip():
        current_app.logger.warning(f"Relatório bruto vazio por {current_user.username}. IP: {request.remote_addr}")
        return jsonify({"erro": "'relatorio_bruto' não pode estar vazio."}), 400
    
    if len(relatorio_bruto) > MAX_INPUT_LENGTH_SERVER:
        current_app.logger.warning(f"Relatório muito longo por {current_user.username}. IP: {request.remote_addr}. Tam: {len(relatorio_bruto)}")
        return jsonify({"erro": f"Relatório muito longo. Máx: {MAX_INPUT_LENGTH_SERVER} chars."}), 413

    try:
        relatorio_processado = report_service_instance.processar_relatorio_com_ia(relatorio_bruto)
        current_app.logger.info(f"Relatório processado para {current_user.username}. IP: {request.remote_addr}. Entrada: {len(relatorio_bruto)}, Saída: {len(relatorio_processado)}")
        return jsonify({'relatorio_processado': relatorio_processado})
    except ValueError as ve: 
        current_app.logger.warning(f"ValueError no processamento para {current_user.username}: {ve}. IP: {request.remote_addr}")
        return jsonify({'erro': str(ve)}), 400 
    except RuntimeError as rte: 
        current_app.logger.error(f"RuntimeError no processamento para {current_user.username}: {rte}. IP: {request.remote_addr}", exc_info=False)
        return jsonify({'erro': str(rte)}), 500 
    except Exception as e: 
        current_app.logger.error(f"Exceção genérica para {current_user.username}: {e.__class__.__name__}: {e}. IP: {request.remote_addr}", exc_info=True)
        return jsonify({'erro': 'Erro interno inesperado. Tente novamente.'}), 500

@main_bp.route('/relatorio_ronda', methods=['GET', 'POST'])
@login_required
def relatorio_ronda_route():
    form = TestarRondasForm() 
    resultado_processado = None
    log_enviado = None

    if form.validate_on_submit():
        log_bruto = form.log_bruto_rondas.data
        
        nome_condominio_selecionado = form.nome_condominio.data
        if nome_condominio_selecionado == 'Outro':
            nome_condominio_final = form.nome_condominio_outro.data
        else:
            nome_condominio_final = nome_condominio_selecionado
        
        data_plantao_obj = form.data_plantao.data 
        data_plantao_str = data_plantao_obj.strftime('%d/%m/%Y') 
            
        escala_plantao_final = form.escala_plantao.data
        
        log_enviado = log_bruto

        try:
            # Certifique-se que a função processar_log_de_rondas está corretamente importada e disponível
            resultado_processado = processar_log_de_rondas(
                log_bruto, 
                nome_condominio_final,
                data_plantao_str,
                escala_plantao_final
            )
            current_app.logger.info(f"Relatório de rondas processado por {current_user.username}.")
            flash('Relatório de rondas processado com sucesso!', 'success')
        except Exception as e:
            current_app.logger.error(f"Erro ao processar relatório de rondas para {current_user.username}: {e}", exc_info=True)
            flash(f'Ocorreu um erro ao processar o relatório de rondas: {str(e)}', 'danger')
            resultado_processado = f"Erro: {str(e)}" # Mostra o erro no template para depuração
    
    elif request.method == 'POST': # Se o formulário não validou mas foi um POST
        current_app.logger.warning(f"Falha na validação do formulário de Relatório de Rondas por {current_user.username}. Erros: {form.errors}")
        log_enviado = form.log_bruto_rondas.data # Mantém o log enviado para o usuário ver

    return render_template('relatorio_ronda.html', 
                           title='Relatório de Ronda', 
                           form=form,
                           resultado=resultado_processado,
                           log_enviado=log_enviado
                          )
