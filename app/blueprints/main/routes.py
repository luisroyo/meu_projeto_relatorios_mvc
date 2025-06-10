# app/blueprints/main/routes.py
import logging
from flask import Blueprint, render_template, current_app, jsonify, request, g
from flask_login import login_required, current_user

# Importar os serviços específicos
from app.services.patrimonial_report_service import PatrimonialReportService
from app.services.email_format_service import EmailFormatService

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# --- INJEÇÃO DE DEPENDÊNCIA (a forma correta) ---

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

# As instâncias globais de serviço foram removidas daqui.

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


@main_bp.route('/processar_relatorio', methods=['POST'])
@login_required
def processar_relatorio():
    try:
        # Usa as funções auxiliares para obter os serviços sob demanda
        patrimonial_service = _get_patrimonial_service()
        email_service = _get_email_service()
    except Exception as e:
        logger.error("Serviços de relatório não foram inicializados corretamente: %s", e)
        return jsonify({'erro': 'Serviço de processamento indisponível no momento.'}), 503

    if not request.is_json:
        logger.warning("Requisição para /processar_relatorio não é JSON.")
        return jsonify({'erro': 'Formato inválido. Envie JSON.'}), 400

    data = request.get_json()
    bruto = data.get('relatorio_bruto')
    format_for_email_checked = data.get('format_for_email', False)

    if not isinstance(bruto, str) or not bruto.strip():
        logger.warning("Relatório bruto ausente ou inválido na requisição.")
        return jsonify({'erro': 'relatorio_bruto é obrigatório e não pode estar vazio.'}), 400

    MAX_CHARS = current_app.config.get('REPORT_MAX_CHARS', 12000)
    if len(bruto) > MAX_CHARS:
        logger.warning(f"Relatório bruto excedeu {MAX_CHARS} caracteres.")
        return jsonify({'erro': f'Relatório muito longo (máximo de {MAX_CHARS} caracteres permitidos).'}), 413

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
        else:
            logger.warning("Nenhum texto disponível para formatação de email.")
            resposta_json['erro_email'] = "Nenhum conteúdo para formatar para e-mail."
    else:
        sucesso_email = True

    status_code = 200 if sucesso_padrao or (format_for_email_checked and sucesso_email) else 500
    
    logger.info(f"Resposta JSON final (status {status_code}): {resposta_json}")
    return jsonify(resposta_json), status_code