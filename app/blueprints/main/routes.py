# app/blueprints/main/routes.py
from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_required, current_user
# Se db e User não forem usados diretamente aqui, podem ser removidos as importações.
# from app import db
# from app.models import User 

# Importar os serviços específicos que serão usados por este blueprint
from app.services.patrimonial_report_service import PatrimonialReportService
from app.services.email_format_service import EmailFormatService 

import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__) # Logger específico para este blueprint

# Instanciar os serviços que este blueprint utilizará.
# Eles herdarão a configuração do modelo Gemini da BaseGenerativeService.
try:
    patrimonial_service = PatrimonialReportService()
    email_service = EmailFormatService() 
except Exception as e:
    # Usar o logger do blueprint ou um logger global da aplicação
    logger.critical(f"Falha ao instanciar serviços no main_bp: {e}", exc_info=True)
    patrimonial_service = None
    email_service = None


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
    if patrimonial_service is None or email_service is None:
        logger.error("Serviços de relatório não foram inicializados corretamente.")
        return jsonify({'erro': 'Serviço de processamento indisponível no momento.'}), 503 # Service Unavailable

    if not request.is_json:
        logger.warning("Requisição para /processar_relatorio não é JSON.")
        return jsonify({'erro': 'Formato inválido. Envie JSON.'}), 400 # Bad Request

    data = request.get_json()
    bruto = data.get('relatorio_bruto')
    format_for_email_checked = data.get('format_for_email', False)

    if not isinstance(bruto, str) or not bruto.strip():
        logger.warning("Relatório bruto ausente ou inválido na requisição.")
        return jsonify({'erro': 'relatorio_bruto é obrigatório e não pode estar vazio.'}), 400 # Bad Request

    # Idealmente, este valor viria da configuração da aplicação
    MAX_CHARS = current_app.config.get('REPORT_MAX_CHARS', 12000) 
    if len(bruto) > MAX_CHARS:
        logger.warning(f"Relatório bruto excedeu {MAX_CHARS} caracteres.")
        return jsonify({'erro': f'Relatório muito longo (máximo de {MAX_CHARS} caracteres permitidos).'}), 413 # Payload Too Large

    resposta_json = {
        'relatorio_processado': None,
        'relatorio_email': None,
        'erro': None,          # Erro específico do relatório padrão
        'erro_email': None     # Erro específico do relatório de e-mail
    }
    
    # Flags para rastrear o sucesso de cada operação
    sucesso_padrao = False
    sucesso_email = False # Considera-se sucesso se não foi solicitado ou se foi gerado com sucesso

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
        texto_para_email = None
        if sucesso_padrao and resposta_json['relatorio_processado']:
            texto_para_email = resposta_json['relatorio_processado']
        elif bruto: # Fallback para o texto bruto se o processamento padrão falhou
            logger.warning("Relatório padrão falhou ou vazio, usando texto bruto original para e-mail.")
            texto_para_email = bruto
            
        if texto_para_email:
            try:
                relatorio_email_formatado = email_service.formatar_para_email(texto_para_email)
                resposta_json['relatorio_email'] = relatorio_email_formatado
                sucesso_email = True # Sucesso na formatação do email
                logger.info("Relatório de e-mail formatado com sucesso.")
            except Exception as e_email:
                logger.error(f"Erro ao formatar relatório para e-mail: {e_email}", exc_info=True)
                resposta_json['erro_email'] = f"Falha ao gerar relatório para e-mail: {str(e_email)}"
                # sucesso_email permanece False
        else:
            logger.warning("Nenhum texto disponível para formatação de email.")
            resposta_json['erro_email'] = "Nenhum conteúdo para formatar para e-mail, pois o relatório bruto estava vazio e o processado falhou."
            # sucesso_email permanece False
    else:
        sucesso_email = True # Não foi solicitado, então não é uma falha

    # Determinar o código de status final
    # Se qualquer operação solicitada foi bem-sucedida, é 200 OK.
    # O cliente pode então verificar os campos 'erro' e 'erro_email' para falhas parciais.
    if sucesso_padrao or (format_for_email_checked and sucesso_email):
        status_code = 200 # OK
    else:
        # Todas as operações solicitadas falharam
        status_code = 500 # Internal Server Error (ou 422 se a culpa for consistentemente da entrada, mas aqui as exceções dos serviços são tratadas como 500)
    
    logger.info(f"Resposta JSON final (status {status_code}): {resposta_json}")
    return jsonify(resposta_json), status_code