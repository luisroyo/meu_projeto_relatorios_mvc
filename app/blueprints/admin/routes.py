# app/blueprints/admin/routes.py
import logging
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, g
)
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_ # Importa 'and_' para condições múltiplas
from datetime import datetime, timedelta, timezone

# Importa o blueprint do __init__.py desta pasta
from . import admin_bp
from app import db
from app.models import User, LoginHistory, Ronda, Colaborador, ProcessingHistory # Importa ProcessingHistory
from app.decorators.admin_required import admin_required
from app.forms import TestarRondasForm, FormatEmailReportForm, ColaboradorForm
from app.services.justificativa_service import JustificativaAtestadoService
from app.services.justificativa_troca_plantao_service import JustificativaTrocaPlantaoService

logger = logging.getLogger(__name__)

# A linha "admin_bp = Blueprint(...)" foi removida daqui e movida para o __init__.py da pasta.

# --- INJEÇÃO DE DEPENDÊNCIA PARA SERVIÇOS DE IA ---
def _get_justificativa_atestado_service():
    if 'justificativa_atestado_service' not in g:
        g.justificativa_atestado_service = JustificativaAtestadoService()
    return g.justificativa_atestado_service

def _get_justificativa_troca_plantao_service():
    if 'justificativa_troca_plantao_service' not in g:
        g.justificativa_troca_plantao_service = JustificativaTrocaPlantaoService()
    return g.justificativa_troca_plantao_service

# --- ROTAS ---

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    logger.info(f"Admin '{current_user.username}' acessou /admin/, redirecionando para /admin/ferramentas.")
    # Redireciona para o novo dashboard de métricas em vez de ferramentas, ou crie uma rota separada para ele.
    # Por enquanto, vou redirecionar para a nova rota de métricas que vamos criar.
    return redirect(url_for('admin.dashboard_metrics'))

@admin_bp.route('/dashboard_metrics')
@login_required
@admin_required
def dashboard_metrics():
    logger.info(f"Admin '{current_user.username}' acessou o dashboard de métricas.")

    # Data de 30 dias atrás para filtrar os dados
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    # 1. Total de usuários registrados (aprovados e pendentes)
    total_users = db.session.query(User).count()
    total_approved_users = db.session.query(User).filter_by(is_approved=True).count()
    total_pending_users = total_users - total_approved_users

    # 2. Histórico de logins (sucessos vs. falhas nos últimos 30 dias)
    successful_logins = db.session.query(LoginHistory).filter(
        and_(LoginHistory.timestamp >= thirty_days_ago,
             LoginHistory.success == True)
    ).count()
    failed_logins = db.session.query(LoginHistory).filter(
        and_(LoginHistory.timestamp >= thirty_days_ago,
             LoginHistory.success == False)
    ).count()
    
    # 3. Processamentos de relatórios (sucessos vs. falhas nos últimos 30 dias)
    successful_reports = db.session.query(ProcessingHistory).filter(
        and_(ProcessingHistory.timestamp >= thirty_days_ago,
             ProcessingHistory.success == True)
    ).count()
    failed_reports = db.session.query(ProcessingHistory).filter(
        and_(ProcessingHistory.timestamp >= thirty_days_ago,
             ProcessingHistory.success == False)
    ).count()

    # 4. Processamentos de relatórios por tipo (nos últimos 30 dias)
    processing_by_type = db.session.query(
        ProcessingHistory.processing_type,
        func.count(ProcessingHistory.id)
    ).filter(
        ProcessingHistory.timestamp >= thirty_days_ago
    ).group_by(
        ProcessingHistory.processing_type
    ).all()
    
    # Converte para um dicionário para facilitar o uso no template/JS
    processing_types_data = {item[0]: item[1] for item in processing_by_type}


    # 5. Atividade de usuários por dia (logins e processamentos nos últimos 30 dias)
    # Logins por dia
    logins_per_day = db.session.query(
        func.date(LoginHistory.timestamp), # Extrai apenas a data
        func.count(LoginHistory.id)
    ).filter(
        LoginHistory.timestamp >= thirty_days_ago
    ).group_by(
        func.date(LoginHistory.timestamp)
    ).order_by(
        func.date(LoginHistory.timestamp)
    ).all()

    # Processamentos por dia
    processing_per_day = db.session.query(
        func.date(ProcessingHistory.timestamp), # Extrai apenas a data
        func.count(ProcessingHistory.id)
    ).filter(
        ProcessingHistory.timestamp >= thirty_days_ago
    ).group_by(
        func.date(ProcessingHistory.timestamp)
    ).order_by(
        func.date(ProcessingHistory.timestamp)
    ).all()

    # Formata os dados de logins e processamentos por dia para o Chart.js
    # Garante que todos os dias no período tenham um valor (0 se não houver atividade)
    date_labels = []
    current_date = thirty_days_ago.date()
    end_date = datetime.now(timezone.utc).date()
    
    while current_date <= end_date:
        date_labels.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    logins_data_map = {str(date): count for date, count in logins_per_day}
    processing_data_map = {str(date): count for date, count in processing_per_day}

    logins_chart_data = [logins_data_map.get(label, 0) for label in date_labels]
    processing_chart_data = [processing_data_map.get(label, 0) for label in date_labels]

    return render_template('admin_dashboard.html',
                           title='Dashboard de Métricas',
                           total_users=total_users,
                           total_approved_users=total_approved_users,
                           total_pending_users=total_pending_users,
                           successful_logins=successful_logins,
                           failed_logins=failed_logins,
                           successful_reports=successful_reports,
                           failed_reports=failed_reports,
                           processing_types_data=processing_types_data,
                           date_labels=date_labels,
                           logins_chart_data=logins_chart_data,
                           processing_chart_data=processing_chart_data
                           )


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

    if not tipo_justificativa or not isinstance(dados_variaveis, dict):
        logger.warning(f"API Processar Justificativa: 'tipo_justificativa' ou 'dados_variaveis' inválidos. Payload: {payload} IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
        return jsonify({'erro': "Dados inválidos: tipo ou dados da justificativa ausentes ou em formato incorreto."}), 400

    logger.info(f"API Processar Justificativa: Tipo='{tipo_justificativa}' Dados='{dados_variaveis}' recebidos por '{current_user.username}'.")

    try:
        if tipo_justificativa == "atestado":
            service = _get_justificativa_atestado_service()
            texto_gerado = service.gerar_justificativa(dados_variaveis)
        elif tipo_justificativa == "troca_plantao":
            service = _get_justificativa_troca_plantao_service()
            texto_gerado = service.gerar_justificativa_troca(dados_variaveis)
        else:
            logger.warning(f"API Processar Justificativa: Tipo de justificativa desconhecido '{tipo_justificativa}'.")
            return jsonify({'erro': f"Tipo de justificativa desconhecido: {tipo_justificativa}"}), 400

        logger.info(f"API Processar Justificativa: Justificativa tipo '{tipo_justificativa}' gerada para '{current_user.username}'.")
        return jsonify({'justificativa_gerada': texto_gerado})

    except ValueError as ve:
        logger.error(f"API Processar Justificativa: Erro de valor ao processar tipo '{tipo_justificativa}' para '{current_user.username}': {ve}", exc_info=True)
        return jsonify({'erro': f'Erro nos dados ou configuração do template: {str(ve)}'}), 400
    except RuntimeError as rte:
        logger.error(f"API Processar Justificativa: Erro de runtime ao processar tipo '{tipo_justificativa}' para '{current_user.username}': {rte}", exc_info=True)
        return jsonify({'erro': f'Erro interno no serviço de IA: {str(rte)}'}), 500
    except NotImplementedError as nie:
        logger.error(f"API Processar Justificativa: Funcionalidade não implementada para tipo '{tipo_justificativa}': {nie}", exc_info=True)
        return jsonify({'erro': str(nie)}), 501
    except Exception as e:
        logger.error(f"API Processar Justificativa: Erro inesperado ao processar tipo '{tipo_justificativa}' para '{current_user.username}': {e}", exc_info=True)
        return jsonify({'erro': f'Erro inesperado ao contatar o serviço de IA: {str(e)}'}), 500

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
        # Exclui o histórico de login e rondas antes de deletar o usuário para evitar erros de chave estrangeira
        LoginHistory.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
        Ronda.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
        # Exclui o histórico de processamento
        ProcessingHistory.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False) # ADIÇÃO
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário {user_to_delete.username} deletado com sucesso.', 'success')
        logger.info(f"Admin '{current_user.username}' deletou o usuário '{user_to_delete.username}' (ID: {user_id}).")
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário {user_to_delete.username}: {str(e)}', 'danger')
        logger.error(f"Erro ao deletar usuário '{user_to_delete.username}' por admin '{current_user.username}': {e}", exc_info=True)
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/colaboradores', methods=['GET'])
@login_required
@admin_required
def listar_colaboradores():
    logger.info(f"Admin '{current_user.username}' acessou a lista de colaboradores.")
    page = request.args.get('page', 1, type=int)
    colaboradores_pagination = Colaborador.query.order_by(Colaborador.nome_completo).paginate(page=page, per_page=10)
    return render_template('admin_listar_colaboradores.html',
                           title='Gerenciar Colaboradores',
                           colaboradores_pagination=colaboradores_pagination)

@admin_bp.route('/api/colaboradores/search', methods=['GET'])
@login_required
@admin_required
def api_search_colaboradores():
    search_term = request.args.get('term', '').strip()

    if not search_term or len(search_term) < 2:
        return jsonify([])

    colaboradores_encontrados = Colaborador.query.filter(
        Colaborador.status == 'Ativo',
        func.lower(Colaborador.nome_completo).contains(func.lower(search_term))
    ).order_by(Colaborador.nome_completo).limit(10).all()

    resultado = [
        {'id': col.id, 'nome_completo': col.nome_completo, 'cargo': col.cargo}
        for col in colaboradores_encontrados
    ]
    return jsonify(resultado)

@admin_bp.route('/api/colaborador/<int:colaborador_id>/details', methods=['GET'])
@login_required
@admin_required
def api_get_colaborador_details(colaborador_id):
    colaborador = Colaborador.query.filter_by(id=colaborador_id, status='Ativo').first()
    if colaborador:
        return jsonify({
            'id': colaborador.id,
            'nome_completo': colaborador.nome_completo,
            'cargo': colaborador.cargo,
            'matricula': colaborador.matricula
        })
    return jsonify({'erro': 'Colaborador não encontrado ou inativo'}), 404

@admin_bp.route('/colaboradores/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def adicionar_colaborador():
    form = ColaboradorForm()
    if form.validate_on_submit():
        try:
            novo_colaborador = Colaborador(
                nome_completo=form.nome_completo.data,
                cargo=form.cargo.data,
                matricula=form.matricula.data if form.matricula.data else None,
                data_admissao=form.data_admissao.data,
                status=form.status.data
            )
            db.session.add(novo_colaborador)
            db.session.commit()
            flash(f'Colaborador "{novo_colaborador.nome_completo}" adicionado com sucesso!', 'success')
            logger.info(f"Admin '{current_user.username}' adicionou novo colaborador: '{novo_colaborador.nome_completo}'.")
            return redirect(url_for('admin.listar_colaboradores'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao adicionar novo colaborador por '{current_user.username}': {e}", exc_info=True)
            flash(f'Erro ao adicionar colaborador: {str(e)}', 'danger')

    elif request.method == 'POST':
        flash('Por favor, corrija os erros no formulário.', 'warning')

    logger.debug(f"Admin '{current_user.username}' acessou o formulário para adicionar novo colaborador.")
    return render_template('admin_colaborador_form.html', title='Adicionar Novo Colaborador', form=form)

@admin_bp.route('/colaboradores/editar/<int:colaborador_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_colaborador(colaborador_id):
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    form = ColaboradorForm(obj=colaborador)

    if form.validate_on_submit():
        if form.matricula.data and form.matricula.data != colaborador.matricula:
            colaborador_existente = Colaborador.query.filter(
                Colaborador.matricula == form.matricula.data,
                Colaborador.id != colaborador_id
            ).first()
            if colaborador_existente:
                form.matricula.errors.append('Esta matrícula já está em uso por outro colaborador.')
                flash('Erro ao salvar: Matrícula já em uso.', 'danger')
                return render_template('admin_colaborador_form.html', title='Editar Colaborador', form=form, colaborador=colaborador)

        try:
            colaborador.nome_completo = form.nome_completo.data
            colaborador.cargo = form.cargo.data
            colaborador.matricula = form.matricula.data if form.matricula.data else None
            colaborador.data_admissao = form.data_admissao.data
            colaborador.status = form.status.data

            db.session.commit()
            flash(f'Colaborador "{colaborador.nome_completo}" atualizado com sucesso!', 'success')
            logger.info(f"Admin '{current_user.username}' editou o colaborador ID {colaborador_id}: '{colaborador.nome_completo}'.")
            return redirect(url_for('admin.listar_colaboradores'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar colaborador ID {colaborador_id} por '{current_user.username}': {e}", exc_info=True)
            flash(f'Erro ao atualizar colaborador: {str(e)}', 'danger')

    elif request.method == 'POST':
        flash('Por favor, corrija os erros no formulário.', 'warning')

    logger.debug(f"Admin '{current_user.username}' acessou o formulário para editar colaborador ID {colaborador_id}.")
    return render_template('admin_colaborador_form.html', title='Editar Colaborador', form=form, colaborador=colaborador)

@admin_bp.route('/colaboradores/deletar/<int:colaborador_id>', methods=['POST'])
@login_required
@admin_required
def deletar_colaborador(colaborador_id):
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    try:
        nome_colaborador = colaborador.nome_completo
        db.session.delete(colaborador)
        db.session.commit()
        flash(f'Colaborador "{nome_colaborador}" deletado com sucesso!', 'success')
        logger.info(f"Admin '{current_user.username}' deletou o colaborador ID {colaborador_id}: '{nome_colaborador}'.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar colaborador ID {colaborador_id} por '{current_user.username}': {e}", exc_info=True)
        flash(f'Erro ao deletar colaborador: {str(e)}. Verifique se há dependências.', 'danger')
    return redirect(url_for('admin.listar_colaboradores'))