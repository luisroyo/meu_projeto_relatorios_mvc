# app/blueprints/main/routes.py
import logging
from flask import Blueprint, render_template, current_app, jsonify, request, g
from flask_login import login_required, current_user

# --- CORREÇÃO: Importar 'limiter' ---
from app import limiter, db # Importa 'db'
from app.models import ProcessingHistory # Importa o novo modelo
from app.services.patrimonial_report_service import PatrimonialReportService
from app.services.email_format_service import EmailFormatService

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

def _get_patrimonial_service():
    """Obtém uma instância de PatrimonialReportService para a requisição atual."""
    if 'patrimonial_service' not in g:
        g.patrimonial_service = PatrimonialReportService()
    return g.patrimonial_service

def _get_email_service():
    """Obtém uma instância de EmailFormatService para a requisição atual."""
    if 'email_service' not in g:
        g.email_service = EmailFormatService()
    return g.email_service

@main_bp.route('/')
@login_required
def index():
    remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.debug(
        f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} "
        f"({current_user.username if current_user.is_authenticated else 'N/A'}). "
        f"IP: {remote_addr}"
    )
    return render_template('index.html', title='Analisador de Relatórios IA')


# --- ADIÇÃO DO DECORATOR DE RATE LIMIT ---
@main_bp.route('/processar_relatorio', methods=['POST'])
@limiter.limit("20 per hour")  # Limita a 20 processamentos por hora por IP
@login_required
def processar_relatorio():
    # Inicializa variáveis para o histórico de processamento
    processing_success = False
    processing_error_message = None

    try:
        patrimonial_service = _get_patrimonial_service()
        email_service = _get_email_service()
    except Exception as e:
        logger.error("Serviços de relatório não foram inicializados corretamente: %s", e)
        processing_error_message = f"Erro na inicialização do serviço: {str(e)}"
        # Salva o histórico mesmo em caso de falha na inicialização do serviço
        if current_user.is_authenticated:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type='patrimonial_report', # Ou um tipo mais genérico se for o caso
                success=False,
                error_message=processing_error_message
            )
            db.session.add(history)
            db.session.commit()
        return jsonify({'erro': 'Serviço de processamento indisponível no momento.'}), 503

    if not request.is_json:
        processing_error_message = 'Formato inválido. Envie JSON.'
        logger.warning(processing_error_message)
        if current_user.is_authenticated:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type='patrimonial_report',
                success=False,
                error_message=processing_error_message
            )
            db.session.add(history)
            db.session.commit()
        return jsonify({'erro': processing_error_message}), 400

    data = request.get_json()
    bruto = data.get('relatorio_bruto')
    format_for_email_checked = data.get('format_for_email', False)

    if not isinstance(bruto, str) or not bruto.strip():
        processing_error_message = 'relatorio_bruto é obrigatório e não pode estar vazio.'
        logger.warning(processing_error_message)
        if current_user.is_authenticated:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type='patrimonial_report',
                success=False,
                error_message=processing_error_message
            )
            db.session.add(history)
            db.session.commit()
        return jsonify({'erro': processing_error_message}), 400

    MAX_CHARS = current_app.config.get('REPORT_MAX_CHARS', 12000)
    if len(bruto) > MAX_CHARS:
        processing_error_message = f'Relatório muito longo (máximo de {MAX_CHARS} caracteres permitidos).'
        logger.warning(f"Relatório bruto excedeu {MAX_CHARS} caracteres.")
        if current_user.is_authenticated:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type='patrimonial_report',
                success=False,
                error_message=processing_error_message
            )
            db.session.add(history)
            db.session.commit()
        return jsonify({'erro': processing_error_message}), 413

    resposta_json = {
        'relatorio_processado': None,
        'relatorio_email': None,
        'erro': None,
        'erro_email': None
    }
    
    sucesso_padrao = False
    sucesso_email = False

    try:
        logger.info("Iniciando processamento do relatório patrimonial...")
        relatorio_padrao = patrimonial_service.gerar_relatorio_seguranca(bruto)
        resposta_json['relatorio_processado'] = relatorio_padrao
        sucesso_padrao = True
        logger.info("Relatório patrimonial processado com sucesso.")
    except Exception as e_standard:
        logger.error(f"Erro ao processar relatório patrimonial: {e_standard}", exc_info=True)
        resposta_json['erro'] = f"Falha ao gerar relatório padrão: {str(e_standard)}"
        processing_error_message = resposta_json['erro'] # Captura o erro para o histórico
    
    if format_for_email_checked:
        logger.info("Iniciando formatação de e-mail...")
        texto_para_email = resposta_json['relatorio_processado'] if sucesso_padrao and resposta_json['relatorio_processado'] else bruto
            
        if texto_para_email:
            try:
                relatorio_email_formatado = email_service.formatar_para_email(texto_para_email)
                resposta_json['relatorio_email'] = relatorio_email_formatado
                sucesso_email = True
                logger.info("Relatório de e-mail formatado com sucesso.")
            except Exception as e_email:
                logger.error(f"Erro ao formatar relatório para e-mail: {e_email}", exc_info=True)
                resposta_json['erro_email'] = f"Falha ao gerar relatório para e-mail: {str(e_email)}"
                processing_error_message = resposta_json['erro_email'] if not processing_error_message else processing_error_message + "; " + resposta_json['erro_email']
        else:
            logger.warning("Nenhum texto disponível para formatação de email.")
            resposta_json['erro_email'] = "Nenhum conteúdo para formatar para e-mail."
            processing_error_message = resposta_json['erro_email'] if not processing_error_message else processing_error_message + "; " + resposta_json['erro_email']
    else:
        sucesso_email = True

    # Determina o sucesso geral do processamento para o registro de histórico
    processing_success = sucesso_padrao and sucesso_email if format_for_email_checked else sucesso_padrao

    # --- Salva o histórico de processamento no banco de dados ---
    if current_user.is_authenticated:
        try:
            history = ProcessingHistory(
                user_id=current_user.id,
                processing_type='patrimonial_report', # Pode ser mais dinâmico se houver outros tipos
                success=processing_success,
                error_message=processing_error_message
            )
            db.session.add(history)
            db.session.commit()
            logger.info(f"Histórico de processamento registrado para o usuário {current_user.id}. Sucesso: {processing_success}")
        except Exception as e_history:
            db.session.rollback()
            logger.error(f"Erro ao salvar histórico de processamento para o usuário {current_user.id}: {e_history}", exc_info=True)
            # Decide se este erro deve impedir a resposta bem-sucedida ao usuário
            if status_code == 200: # Se a lógica do relatório foi ok, mas o histórico falhou, não retorna 500
                logger.warning("Erro ao salvar histórico, mas o processamento principal foi bem-sucedido.")
            else: # Se já havia erro, adiciona ao erro existente
                resposta_json['erro'] = f"Falha interna (falha ao registrar histórico): {str(e_history)}"
                status_code = 500

    status_code = 200 if (sucesso_padrao or resposta_json['relatorio_email']) and not (resposta_json['erro'] and resposta_json['erro_email']) else 500
    
    logger.info(f"Resposta JSON final (status {status_code}): {resposta_json}")
    return jsonify(resposta_json), status_code