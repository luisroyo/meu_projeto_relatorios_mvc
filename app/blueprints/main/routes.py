# app/blueprints/main/routes.py
from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_required, current_user
# Se db e User não forem usados diretamente aqui, podem ser removidos as importações.
# from app import db
# from app.models import User 

# Importar os serviços específicos que serão usados por este blueprint
from app.services.patrimonial_report_service import PatrimonialReportService # Você precisará criar este serviço
from app.services.email_format_service import EmailFormatService     # Você precisará criar este serviço

import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Instanciar os serviços que este blueprint utilizará.
# Eles herdarão a configuração do modelo Gemini da BaseGenerativeService.
# A instanciação dos serviços permanece a mesma
try:
    patrimonial_service = PatrimonialReportService()
    email_service = EmailFormatService() # Garanta que este é o serviço correto (Gemini)
except Exception as e:
    logger.critical(f"Falha ao instanciar serviços no main_bp: {e}", exc_info=True)
    patrimonial_service = None
    email_service = None


@main_bp.route('/')
@login_required
def index():
    logger.debug(
        f"Acessando rota /. Usuário autenticado: {current_user.is_authenticated} "
        f"({current_user.username if current_user.is_authenticated else 'N/A'}). "
        f"IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}"
    )
    return render_template('index.html', title='Analisador de Relatórios IA')


@main_bp.route('/processar_relatorio', methods=['POST'])
@login_required
def processar_relatorio():
    if patrimonial_service is None or email_service is None:
        logger.error("Serviços de relatório não foram inicializados corretamente.")
        return jsonify({'erro': 'Serviço de processamento indisponível no momento.'}), 503

    if not request.is_json:
        current_app.logger.warning("Requisição para /processar_relatorio não é JSON.")
        return jsonify({'erro': 'Formato inválido. Envie JSON.'}), 400

    data = request.get_json()
    bruto = data.get('relatorio_bruto')
    format_for_email_checked = data.get('format_for_email', False)

    if not isinstance(bruto, str) or not bruto.strip():
        current_app.logger.warning("Relatório bruto ausente ou inválido na requisição.")
        return jsonify({'erro': 'relatorio_bruto inválido.'}), 400

    MAX_CHARS = 12000 
    if len(bruto) > MAX_CHARS:
        current_app.logger.warning(f"Relatório bruto excedeu {MAX_CHARS} caracteres.")
        return jsonify({'erro': f'Relatório muito longo (máx {MAX_CHARS} caracteres).'}), 413

    resposta_json = {
        'relatorio_processado': None,
        'relatorio_email': None,
        'erro': None,
        'erro_email': None 
    }
    
    erro_standard_msg = None

    try:
        # 1. Gerar o relatório padrão (patrimonial) com o serviço específico
        current_app.logger.info("Iniciando processamento do relatório patrimonial...")
        # O método em PatrimonialReportService pode se chamar, por exemplo, gerar_relatorio_seguranca
        # e esperar 'bruto' como uma string, se o template dele for formatado com {dados_brutos}
        relatorio_padrao = patrimonial_service.gerar_relatorio_seguranca(bruto) 
        resposta_json['relatorio_processado'] = relatorio_padrao
        current_app.logger.info("Relatório patrimonial processado com sucesso.")

    except Exception as e_standard:
        current_app.logger.error(f"Erro ao processar relatório patrimonial: {e_standard}", exc_info=True)
        erro_standard_msg = f"Falha ao gerar relatório patrimonial: {str(e_standard)}"
        resposta_json['erro'] = erro_standard_msg
    
    # 2. Se solicitado, gerar o relatório de e-mail
    if format_for_email_checked:
        current_app.logger.info("Iniciando formatação de e-mail...")
        try:
            # O método em EmailFormatService pode se chamar, por exemplo, formatar_para_email
            # e também esperar 'bruto' como uma string, se o template dele for formatado com {texto_original} ou similar
            texto_para_email = resposta_json['relatorio_processado'] if resposta_json['relatorio_processado'] else bruto
            
            # Se o relatório padrão falhou, você pode optar por não tentar formatar para email
            # ou tentar formatar o 'bruto' original. Aqui, vamos tentar formatar o que tivermos.
            if not texto_para_email and erro_standard_msg:
                 current_app.logger.warning("Relatório padrão falhou, tentando formatar o 'bruto' original para email.")
                 texto_para_email = bruto # Fallback para o bruto original se o processado falhou

            if texto_para_email: # Só tenta formatar se tiver algo para formatar
                relatorio_email_formatado = email_service.formatar_para_email(texto_para_email)
                resposta_json['relatorio_email'] = relatorio_email_formatado
                current_app.logger.info("Relatório de e-mail formatado com sucesso.")
            else:
                current_app.logger.warning("Nenhum texto disponível para formatação de email (relatório padrão falhou e bruto estava vazio).")
                # Não definimos erro_email aqui, pois o erro principal já foi capturado.
                # Ou, se preferir, pode adicionar um erro específico.
                if not resposta_json['erro_email']: # Só adiciona se não houver erro de email já
                     resposta_json['erro_email'] = "Nenhum conteúdo para formatar para email."


        except Exception as e_email:
            current_app.logger.error(f"Erro ao formatar relatório para e-mail: {e_email}", exc_info=True)
            resposta_json['erro_email'] = f"Falha ao gerar relatório para e-mail: {str(e_email)}"
            
    # Determinar o status code final
    # Se houve erro no principal e nada mais foi bem-sucedido ou solicitado, retorna erro
    if erro_standard_msg and not resposta_json['relatorio_processado']:
        if not format_for_email_checked or (format_for_email_checked and resposta_json['erro_email']):
            # Erro no padrão, e (não pediu email OU (pediu email E email também falhou))
            # O status code poderia ser determinado pela natureza do erro_standard_msg
            return jsonify(resposta_json), 500 # Ou 400 dependendo do erro
            
    return jsonify(resposta_json)
