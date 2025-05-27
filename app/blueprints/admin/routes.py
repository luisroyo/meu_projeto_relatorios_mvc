# app/blueprints/admin/routes.py
from flask import (
    Blueprint, render_template, redirect, url_for, flash, 
    request, current_app, jsonify, render_template_string
)
from flask_login import login_required, current_user
from app import db
from app.models import User, LoginHistory, Ronda 
from app.decorators.admin_required import admin_required 
from app.forms import TestarRondasForm, FormatEmailReportForm 
import logging
import os 
from pathlib import Path # Para carregar os templates de prompt de forma robusta

# Importe o seu serviço de IA. Assumindo que é o ReportService para Gemini.
from app.services.report_service import ReportService 

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Define o diretório base para os templates de prompt
# __file__ é o caminho para este arquivo (app/blueprints/admin/routes.py)
# .parent é app/blueprints/admin/
# .parent.parent é app/blueprints/
# .parent.parent.parent é app/  <- CORREÇÃO AQUI
PROMPT_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / 'services' / 'prompt_templates'

def carregar_prompt_template(nome_arquivo_template):
    """Carrega o conteúdo de um arquivo de template de prompt."""
    try:
        caminho_template = PROMPT_TEMPLATE_DIR / nome_arquivo_template
        logger.debug(f"Tentando carregar template de prompt de: {caminho_template}")
        with open(caminho_template, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Arquivo de template de prompt NÃO ENCONTRADO: {caminho_template}")
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar template de prompt '{nome_arquivo_template}': {e}", exc_info=True)
        return None

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    logger.info(f"Admin '{current_user.username}' acessou /admin/, redirecionando para /admin/ferramentas.")
    return redirect(url_for('admin.admin_tools'))

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    logger.info(f"Admin '{current_user.username}' acessou /admin/users. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
    page = request.args.get('page', 1, type=int)
    users_pagination_obj = User.query.order_by(User.date_registered.desc()).paginate(page=page, per_page=10)
    return render_template('admin_users.html', title='Gerenciar Usuários', users_pagination=users_pagination_obj)

@admin_bp.route('/ferramentas', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_tools():
    ronda_form_instance = TestarRondasForm(prefix="ronda_form") 
    email_form_instance = FormatEmailReportForm(prefix="email_form")
    formatted_email_report_text = None

    if request.method == 'POST' and request.form.get('tool_action') == 'format_email':
        email_form_instance = FormatEmailReportForm(request.form, prefix="email_form")
        if email_form_instance.validate_on_submit():
            raw_report = email_form_instance.raw_report.data
            include_greeting = email_form_instance.include_greeting.data
            custom_greeting = email_form_instance.custom_greeting.data.strip()
            include_closing = email_form_instance.include_closing.data
            custom_closing = email_form_instance.custom_closing.data.strip()
            
            parts = []
            if custom_greeting: parts.append(custom_greeting)
            elif include_greeting: parts.append("Prezados(as),")
            if parts: parts.append("") 
            parts.append(raw_report)
            if raw_report.strip() and (custom_closing or include_closing): parts.append("")
            if custom_closing: parts.append(custom_closing)
            elif include_closing: parts.append("Atenciosamente,\nEquipe Administrativa")
            formatted_email_report_text = "\n".join(parts)
            flash('Relatório formatado para e-mail com sucesso!', 'success')
        else:
            flash('Erro na formatação do e-mail. Verifique os campos.', 'danger')

    logger.info(f"Admin '{current_user.username}' acessou/interagiu com o dashboard de ferramentas /admin/ferramentas. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
    return render_template('admin_ferramentas.html', 
                           title='Ferramentas Administrativas',
                           ronda_form=ronda_form_instance,
                           email_form=email_form_instance,
                           formatted_email_report=formatted_email_report_text)

@admin_bp.route('/ferramentas/gerador-justificativas', methods=['GET'])
@login_required
@admin_required
def gerador_justificativas_tool():
    logger.info(f"Admin '{current_user.username}' acessou o Gerador de Justificativas.")
    return render_template('admin_gerador_justificativas.html', title='Gerador de Justificativas iFractal')

@admin_bp.route('/ferramentas/api/processar-justificativa', methods=['POST'])
@login_required
@admin_required
def api_processar_justificativa():
    payload = request.get_json()
    if not payload:
        logger.warning(f"API Processar Justificativa: JSON vazio recebido. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
        return jsonify({'erro': 'Dados não fornecidos.'}), 400

    tipo_justificativa = payload.get('tipo_justificativa')
    dados_variaveis = payload.get('dados_variaveis')

    if not tipo_justificativa or not dados_variaveis:
        logger.warning(f"API Processar Justificativa: 'tipo_justificativa' ou 'dados_variaveis' não encontrados no JSON. Payload: {payload} IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
        return jsonify({'erro': 'Dados inválidos: tipo ou dados da justificativa não encontrados.'}), 400

    logger.info(f"API Processar Justificativa: Tipo='{tipo_justificativa}' Dados='{dados_variaveis}' recebidos por '{current_user.username}'.")

    nome_arquivo_template_prompt = None
    if tipo_justificativa == "atestado":
        nome_arquivo_template_prompt = "justificativa_atestado_medico_template.txt"
    elif tipo_justificativa == "troca_plantao":
        nome_arquivo_template_prompt = "justificativa_troca_plantao_template.txt"
    elif tipo_justificativa == "atraso":
        nome_arquivo_template_prompt = "justificativa_atraso_template.txt" 
    
    if not nome_arquivo_template_prompt:
        logger.warning(f"API Processar Justificativa: Tipo de justificativa desconhecido '{tipo_justificativa}'.")
        return jsonify({'erro': f"Tipo de justificativa desconhecido: {tipo_justificativa}"}), 400

    template_prompt_str = carregar_prompt_template(nome_arquivo_template_prompt)
    if not template_prompt_str:
        logger.error(f"API Processar Justificativa: Falha ao carregar template de prompt '{nome_arquivo_template_prompt}' para tipo '{tipo_justificativa}'. Caminho esperado: {PROMPT_TEMPLATE_DIR / nome_arquivo_template_prompt}")
        return jsonify({'erro': "Erro interno ao carregar modelo de prompt."}), 500

    try:
        prompt_final_para_ia = render_template_string(template_prompt_str, **dados_variaveis)
        logger.debug(f"API Processar Justificativa: Prompt final para IA ('{tipo_justificativa}'):\n{prompt_final_para_ia}")

        report_service = ReportService() 
        texto_gerado = report_service.processar_relatorio_com_ia(prompt_final_para_ia) 
        
        logger.info(f"API Processar Justificativa: Justificativa tipo '{tipo_justificativa}' gerada para '{current_user.username}'.")
        return jsonify({'justificativa_gerada': texto_gerado})
    except Exception as e:
        logger.error(f"API Processar Justificativa: Erro ao processar tipo '{tipo_justificativa}' para '{current_user.username}': {e}", exc_info=True)
        return jsonify({'erro': f'Erro ao contatar o serviço de IA ou processar o template: {str(e)}'}), 500

# ROTAS DE GERENCIAMENTO DE USUÁRIOS
@admin_bp.route('/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_approved:
        user.is_approved = True
        db.session.commit()
        flash(f'Usuário {user.username} aprovado com sucesso.', 'success')
        logger.info(f"Admin '{current_user.username}' aprovou o usuário '{user.username}' (ID: {user.id}).")
    else:
        flash(f'Usuário {user.username} já está aprovado.', 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/revoke', methods=['POST'])
@login_required
@admin_required
def revoke_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode revogar sua própria aprovação.', 'danger')
        logger.warning(f"Admin '{current_user.username}' tentou revogar a própria aprovação.")
        return redirect(url_for('admin.manage_users'))
    
    if user.is_approved:
        user.is_approved = False
        db.session.commit()
        flash(f'Aprovação de {user.username} foi revogada.', 'success')
        logger.info(f"Admin '{current_user.username}' revogou a aprovação do usuário '{user.username}' (ID: {user.id}).")
    else:
        flash(f'Aprovação do usuário {user.username} já estava revogada/pendente.', 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode alterar seu próprio status de administrador.', 'warning')
        logger.warning(f"Admin '{current_user.username}' tentou alterar o próprio status de admin.")
        return redirect(url_for('admin.manage_users'))

    user.is_admin = not user.is_admin
    if user.is_admin and not user.is_approved:
        user.is_approved = True
        flash(f'Usuário {user.username} também foi aprovado automaticamente ao se tornar admin.', 'info')
        logger.info(f"Usuário '{user.username}' (ID: {user.id}) aprovado automaticamente ao se tornar admin.")

    db.session.commit()
    status = "promovido a administrador" if user.is_admin else "rebaixado de administrador"
    flash(f'Usuário {user.username} foi {status} com sucesso.', 'success')
    logger.info(f"Admin '{current_user.username}' alterou o status de admin do usuário '{user.username}' (ID: {user.id}) para: {user.is_admin}.")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash('Você não pode deletar sua própria conta.', 'danger')
        logger.warning(f"Admin '{current_user.username}' tentou deletar a própria conta.")
        return redirect(url_for('admin.manage_users'))
    try:
        LoginHistory.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
        Ronda.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False) 
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário {user_to_delete.username} deletado com sucesso.', 'success')
        logger.info(f"Admin '{current_user.username}' deletou o usuário '{user_to_delete.username}' (ID: {user_id}).")
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário {user_to_delete.username}: {str(e)}', 'danger')
        logger.error(f"Erro ao deletar usuário '{user_to_delete.username}' por admin '{current_user.username}': {e}", exc_info=True)
    return redirect(url_for('admin.manage_users'))
