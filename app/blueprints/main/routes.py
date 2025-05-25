# app/blueprints/main/routes.py
from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_required, current_user
# Se db e User não forem usados diretamente aqui, podem ser removidos as importações.
# from app import db
# from app.models import User 

# Usaremos apenas o ReportService (Gemini)
from app.services.report_service import ReportService

import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Instanciar o ReportService (que usa Gemini e pode carregar ambos os prompts)
report_service = ReportService()


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
        'relatorio_email': None, # Ainda manteremos a estrutura para o frontend
        'erro': None,
        'erro_email': None 
    }

    try:
        # 1. Gerar o relatório padrão com Gemini
        current_app.logger.info("Iniciando processamento do relatório padrão com Gemini...")
        relatorio_padrao = report_service.processar_relatorio_com_ia(bruto, prompt_type="standard")
        resposta_json['relatorio_processado'] = relatorio_padrao
        current_app.logger.info("Relatório padrão processado com sucesso pelo Gemini.")

    except Exception as e_standard: # Captura qualquer erro do processamento padrão
        current_app.logger.error(f"Erro ao processar relatório padrão (Gemini): {e_standard}", exc_info=True)
        resposta_json['erro'] = f"Falha ao gerar relatório padrão (Gemini): {str(e_standard)}"
        # Se o padrão falhar, não tentamos o de e-mail e retornamos o erro.
        # Ou você pode decidir tentar o de e-mail mesmo assim. Por simplicidade, vamos parar aqui se o padrão falhar.
        # Contudo, se o objetivo é sempre tentar o email se solicitado, mesmo que o padrão falhe, a lógica seria diferente.
        # Assumindo que se o padrão falha, não faz sentido prosseguir para o email com o mesmo serviço.
        # Mas como você quer os dois, vamos continuar e tentar o de email.
    
    # 2. Se solicitado, gerar o relatório de e-mail TAMBÉM COM GEMINI
    if format_for_email_checked:
        current_app.logger.info("Iniciando formatação de e-mail com Gemini...")
        try:
            # Usando o mesmo report_service, mas com o prompt_type="email"
            relatorio_email_formatado = report_service.processar_relatorio_com_ia(bruto, prompt_type="email")
            resposta_json['relatorio_email'] = relatorio_email_formatado
            current_app.logger.info("Relatório de e-mail formatado com sucesso pelo Gemini.")
        except Exception as e_email:
            current_app.logger.error(f"Erro ao formatar relatório para e-mail (Gemini): {e_email}", exc_info=True)
            resposta_json['erro_email'] = f"Falha ao gerar relatório para e-mail (Gemini): {str(e_email)}"
            # Nota: O relatório padrão ainda pode estar em resposta_json['relatorio_processado']
            
    # Se houve um erro no processamento padrão e não há relatório padrão,
    # e não foi solicitado email ou o email também falhou, então retorne um erro mais genérico.
    if resposta_json['erro'] and not resposta_json['relatorio_processado'] and \
       (not format_for_email_checked or (format_for_email_checked and not resposta_json['relatorio_email'])):
        # Todos os processamentos solicitados falharam ou o principal falhou e nada mais foi solicitado/bem-sucedido
        status_code = 400 if isinstance(e_standard, ValueError) else 500 # e_standard pode não estar definida se o erro foi no bloco de email
        return jsonify(resposta_json), status_code # Retorna o que foi acumulado

    return jsonify(resposta_json)

