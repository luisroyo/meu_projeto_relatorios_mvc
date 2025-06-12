# app/blueprints/admin/routes.py
import logging
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, g
)
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_, case, cast, Float, BigInteger
from datetime import datetime, timedelta, timezone

from . import admin_bp
from app import db
from app.models import User, LoginHistory, Ronda, Colaborador, ProcessingHistory, Condominio
from app.decorators.admin_required import admin_required
from app.forms import TestarRondasForm, FormatEmailReportForm, ColaboradorForm
from app.services.justificativa_service import JustificativaAtestadoService
from app.services.justificativa_troca_plantao_service import JustificativaTrocaPlantaoService

logger = logging.getLogger(__name__)


def _get_justificativa_atestado_service():
    if 'justificativa_atestado_service' not in g:
        g.justificativa_atestado_service = JustificativaAtestadoService()
    return g.justificativa_atestado_service


def _get_justificativa_troca_plantao_service():
    if 'justificativa_troca_plantao_service' not in g:
        g.justificativa_troca_plantao_service = JustificativaTrocaPlantaoService()
    return g.justificativa_troca_plantao_service


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    logger.info(f"Admin '{current_user.username}' acessou /admin/, redirecionando para /admin/dashboard_metrics.")
    return redirect(url_for('admin.dashboard_metrics'))


@admin_bp.route('/dashboard_metrics')
@login_required
@admin_required
def dashboard_metrics():
    logger.info(f"Admin '{current_user.username}' acessou o dashboard de métricas.")

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    total_users = db.session.query(User).count()
    total_approved_users = db.session.query(User).filter_by(is_approved=True).count()
    total_pending_users = total_users - total_approved_users

    successful_logins = db.session.query(LoginHistory).filter(
        and_(LoginHistory.timestamp >= thirty_days_ago,
             LoginHistory.success == True)
    ).count()
    failed_logins = db.session.query(LoginHistory).filter(
        and_(LoginHistory.timestamp >= thirty_days_ago,
             LoginHistory.success == False)
    ).count()
    
    successful_reports = db.session.query(ProcessingHistory).filter(
        and_(ProcessingHistory.timestamp >= thirty_days_ago,
             ProcessingHistory.success == True)
    ).count()
    failed_reports = db.session.query(ProcessingHistory).filter(
        and_(ProcessingHistory.timestamp >= thirty_days_ago,
             ProcessingHistory.success == False)
    ).count()

    processing_by_type = db.session.query(
        ProcessingHistory.processing_type,
        func.count(ProcessingHistory.id)
    ).filter(
        ProcessingHistory.timestamp >= thirty_days_ago
    ).group_by(
        ProcessingHistory.processing_type
    ).all()
    
    processing_types_data = {item[0]: item[1] for item in processing_by_type}

    logins_per_day = db.session.query(
        func.date(LoginHistory.timestamp),
        func.count(LoginHistory.id)
    ).filter(
        LoginHistory.timestamp >= thirty_days_ago
    ).group_by(
        func.date(LoginHistory.timestamp)
    ).order_by(
        func.date(LoginHistory.timestamp)
    ).all()

    processing_per_day = db.session.query(
        func.date(ProcessingHistory.timestamp),
        func.count(ProcessingHistory.id)
    ).filter(
        ProcessingHistory.timestamp >= thirty_days_ago
    ).group_by(
        func.date(ProcessingHistory.timestamp)
    ).order_by(
        func.date(ProcessingHistory.timestamp)
    ).all()

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


@admin_bp.route('/ronda_dashboard')
@login_required
@admin_required
def ronda_dashboard():
    logger.info(f"Admin '{current_user.username}' acessou o dashboard de rondas.")

    # 1. Rondas por Condomínio
    rondas_por_condominio = db.session.query(
        Condominio.nome,
        func.sum(Ronda.total_rondas_no_log)
    ).outerjoin(Ronda, Ronda.condominio_id == Condominio.id).group_by(Condominio.nome).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()

    condominio_labels = [item[0] for item in rondas_por_condominio]
    rondas_por_condominio_data = [item[1] if item[1] is not None else 0 for item in rondas_por_condominio]

    # 2. Duração Média das Rondas por Condomínio
    # Lógica condicional para funcionar em PostgreSQL (Render) e SQLite (local)
    if db.engine.dialect.name == 'postgresql':
        # Função específica do PostgreSQL para obter a diferença em segundos
        diff_seconds = func.extract('epoch', Ronda.ultimo_evento_log_dt - Ronda.primeiro_evento_log_dt)
    else:
        # Função para SQLite e outros bancos
        diff_seconds = func.strftime('%s', Ronda.ultimo_evento_log_dt).cast(BigInteger) - func.strftime('%s', Ronda.primeiro_evento_log_dt).cast(BigInteger)
    
    diff_minutes = diff_seconds / 60.0
    
    duracao_media_por_condominio_raw = db.session.query(
        Condominio.nome,
        func.avg(diff_minutes)
    ).outerjoin(Ronda, Ronda.condominio_id == Condominio.id).filter(
        Ronda.primeiro_evento_log_dt.isnot(None),
        Ronda.ultimo_evento_log_dt.isnot(None)
    ).group_by(Condominio.nome).order_by(func.avg(diff_minutes).desc()).all()

    duracao_condominio_labels = [item[0] for item in duracao_media_por_condominio_raw]
    duracao_media_data = [round(item[1], 2) if item[1] is not None else 0 for item in duracao_media_por_condominio_raw]

    # 3. Rondas por Turno (Geral)
    rondas_por_turno = db.session.query(
        Ronda.turno_ronda,
        func.sum(Ronda.total_rondas_no_log)
    ).filter(
        Ronda.turno_ronda.isnot(None), Ronda.total_rondas_no_log.isnot(None)
    ).group_by(Ronda.turno_ronda).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()

    turno_labels = [item[0] for item in rondas_por_turno]
    rondas_por_turno_data = [item[1] if item[1] is not None else 0 for item in rondas_por_turno]

    # 4. Rondas por Supervisor
    rondas_por_supervisor = db.session.query(
        User.username,
        func.sum(Ronda.total_rondas_no_log)
    ).outerjoin(Ronda, User.id == Ronda.user_id).filter(
        User.is_approved == True
    ).group_by(User.username).order_by(func.sum(Ronda.total_rondas_no_log).desc()).all()

    supervisor_labels = [item[0] for item in rondas_por_supervisor]
    rondas_por_supervisor_data = [item[1] if item[1] is not None else 0 for item in rondas_por_supervisor]

    # 5. Total de Rondas ao Longo do Tempo (Últimos 30 dias)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    rondas_por_dia = db.session.query(
        func.date(Ronda.data_plantao_ronda),
        func.sum(Ronda.total_rondas_no_log)
    ).filter(
        Ronda.data_plantao_ronda >= thirty_days_ago.date(),
        Ronda.total_rondas_no_log.isnot(None)
    ).group_by(
        func.date(Ronda.data_plantao_ronda)
    ).order_by(
        func.date(Ronda.data_plantao_ronda)
    ).all()

    ronda_date_labels = []
    ronda_activity_data = []
    current_date = thirty_days_ago.date()
    end_date = datetime.now(timezone.utc).date()

    rondas_by_date_map = {str(date): count if count is not None else 0 for date, count in rondas_por_dia}

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        ronda_date_labels.append(date_str)
        ronda_activity_data.append(rondas_by_date_map.get(date_str, 0))
        current_date += timedelta(days=1)

    return render_template('admin_ronda_dashboard.html',
                           title='Dashboard de Métricas de Rondas',
                           condominio_labels=condominio_labels,
                           rondas_por_condominio_data=rondas_por_condominio_data,
                           duracao_condominio_labels=duracao_condominio_labels,
                           duracao_media_data=duracao_media_data,
                           turno_labels=turno_labels,
                           rondas_por_turno_data=rondas_por_turno_data,
                           supervisor_labels=supervisor_labels,
                           rondas_por_supervisor_data=rondas_por_supervisor_data,
                           ronda_date_labels=ronda_date_labels,
                           ronda_activity_data=ronda_activity_data
                           )


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    logger.info(f"Admin '{current_user.username}' acessou /admin/users. IP: {request.remote_addr if hasattr(request, 'remote_addr') else 'N/A'}")
    page = request.args.get('page', 1, type=int)
    users_pagination_obj = User.query.order_by(User.date_registered.desc()).paginate(page=page, per_page=10)
    return render_template('admin_users.html', title='Gerenciar Usuários', users_pagination=users_pagination_obj)


@admin_bp.route('/ferramentas', methods=['GET'])
@login_required
@admin_required
def admin_tools():
    logger.info(f"Admin '{current_user.username}' acessou o menu de ferramentas /admin/ferramentas.")
    return render_template('admin_ferramentas.html', title='Ferramentas Administrativas')


@admin_bp.route('/ferramentas/formatar-email', methods=['GET', 'POST'])
@login_required
@admin_required
def format_email_report_tool():
    form = FormatEmailReportForm()
    formatted_report = None
    if form.validate_on_submit():
        raw_report = form.raw_report.data
        include_greeting = form.include_greeting.data
        custom_greeting = form.custom_greeting.data.strip()
        include_closing = form.include_closing.data
        custom_closing = form.custom_closing.data.strip()

        parts = []
        if custom_greeting:
            parts.append(custom_greeting)
        elif include_greeting:
            parts.append("Prezados(as),")
        
        if parts:
            parts.append("")
        parts.append(raw_report)
        if raw_report.strip() and (custom_closing or include_closing):
            parts.append("")
        
        if custom_closing:
            parts.append(custom_closing)
        elif include_closing:
            parts.append("Atenciosamente,\nEquipe Administrativa")
        
        formatted_report = "\n".join(parts)
        flash('Relatório formatado para e-mail com sucesso!', 'success')
    
    return render_template('admin_formatar_email.html', 
                           title='Formatar Relatório para E-mail', 
                           form=form, 
                           formatted_report=formatted_report)


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
        LoginHistory.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
        Ronda.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
        ProcessingHistory.query.filter_by(user_id=user_to_delete.id).delete(synchronize_session=False)
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
        flash(f'Erro ao deletar colaborador: {str(e)}. Verifique se há dependências.', 'danger')
        logger.error(f"Erro ao deletar colaborador ID {colaborador_id} por '{current_user.username}': {e}", exc_info=True)
    return redirect(url_for('admin.listar_colaboradores'))