from flask import (
    render_template, request, jsonify, redirect, url_for, flash,
    Blueprint, current_app
)
from app import db
from app.services.report_service import ReportService
from app.services.ronda_service import processar_log_de_rondas
# A linha abaixo já inclui TestarRondasForm, o que é ótimo.
from app.forms import RegistrationForm, LoginForm, TestarRondasForm 
from app.models import User, LoginHistory
from flask_login import login_user, current_user, logout_user, login_required
from urllib.parse import urlsplit
import logging
from datetime import datetime, timezone # Certifique-se que timezone está importado

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

report_service_instance = None
try:
    report_service_instance = ReportService()
    logger.info("Instância de ReportService criada em routes.py (nível global do blueprint)")
except (ValueError, RuntimeError) as e:
    logger.critical(f"Falha na inicialização do ReportService em routes.py: {e}", exc_info=True)


@main_bp.route('/')
@login_required
def index():
    current_app.logger.debug(f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} ({current_user.username})")
    return render_template('index.html', title='Processador de Relatórios')

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
        current_app.logger.info(f"Usuário já autenticado ({current_user.username}) tentou acessar /login. Redirecionando para index.")
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        login_success = False
        user_id_for_log = None

        current_app.logger.debug(f"Tentativa de login para email: {form.email.data}. Usuário encontrado: {'Sim' if user else 'Não'}")

        if user and user.check_password(form.password.data):
            current_app.logger.info(f"Verificação de senha para {user.username} bem-sucedida.")
            login_user(user, remember=form.remember.data)
            current_app.logger.info(f"Usuário {user.username} AGORA autenticado: {current_user.is_authenticated}")
            login_success = True
            user_id_for_log = user.id
            flash(f'Login bem-sucedido, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            current_app.logger.debug(f"Parâmetro next_page do login: {next_page}")
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.index')
            current_app.logger.info(f"Redirecionando usuário {user.username} para: {next_page} após login.")
            return redirect(next_page)
        else:
            if user: 
                current_app.logger.warning(f"Tentativa de login falhou para o usuário {user.username} (email: {form.email.data}). Senha incorreta. IP: {request.remote_addr}")
                user_id_for_log = user.id
            else: 
                current_app.logger.warning(f"Tentativa de login falhou. Email não encontrado: {form.email.data}. IP: {request.remote_addr}")
            
            flash('Login falhou. Verifique seu email e senha.', 'danger')
        
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


# MODIFIED SECTION - testar_rondas_route
@main_bp.route('/testar_rondas', methods=['GET', 'POST'])
@login_required
def testar_rondas_route():
    form = TestarRondasForm() # Instancia o novo formulário
    resultado_processado = None
    log_enviado = None # Para manter o log no textarea após o POST

    # Se o método for GET e houver valores padrão que você queira definir dinamicamente
    # (além dos defaults da classe do formulário), você pode fazer aqui.
    # Ex: form.nome_condominio.data = "Valor Padrão GET"
    # No entanto, os defaults definidos na classe TestarRondasForm já serão aplicados.

    if form.validate_on_submit(): # Processa no POST se o formulário for válido
        log_bruto = form.log_bruto_rondas.data
        nome_condominio = form.nome_condominio.data
        data_plantao = form.data_plantao.data
        escala_plantao = form.escala_plantao.data
        log_enviado = log_bruto # Mantém o log no textarea

        try:
            resultado_processado = processar_log_de_rondas(
                log_bruto, 
                nome_condominio,
                data_plantao,
                escala_plantao
            )
            current_app.logger.info(f"Teste de processamento de rondas executado por {current_user.username}.")
            flash('Log de rondas processado com sucesso!', 'success')
        except Exception as e:
            current_app.logger.error(f"Erro ao testar processamento de rondas para {current_user.username}: {e}", exc_info=True)
            flash(f'Ocorreu um erro ao processar o log de rondas: {str(e)}', 'danger')
            resultado_processado = f"Erro: {str(e)}" # Passa a mensagem de erro para o template
            # Em caso de erro no processamento, os dados do formulário (form.data) já conterão o que o usuário enviou
            # e serão repopulados no template.
    
    elif request.method == 'POST': # Se validate_on_submit() falhou
        current_app.logger.warning(f"Falha na validação do formulário de Testar Rondas por {current_user.username}. Erros: {form.errors}")
        log_enviado = form.log_bruto_rondas.data # Mantém o log no textarea mesmo com erro de validação
        # Os erros de validação (form.errors) serão automaticamente exibidos no template se configurado corretamente.

    # Para GET ou se a validação do POST falhar (ou após processamento bem-sucedido/com erro)
    # Renderiza o template, passando o objeto form e quaisquer resultados/logs.
    return render_template('testar_rondas.html', 
                           title='Testar Processamento de Rondas', 
                           form=form,
                           resultado=resultado_processado,
                           log_enviado=log_enviado 
                          )