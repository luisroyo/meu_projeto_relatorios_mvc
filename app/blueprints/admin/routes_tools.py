# app/blueprints/admin/routes_tools.py
import logging
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, g
)
from flask_login import login_required, current_user
from sqlalchemy import func, and_, cast, Float
from datetime import datetime, timedelta, timezone

from app.services.escala_service import get_escala_mensal, salvar_escala_mensal

from . import admin_bp
from app import db
from app.models import User, LoginHistory, Ronda, Colaborador, ProcessingHistory, Condominio, EscalaMensal
from app.decorators.admin_required import admin_required
from app.forms import FormatEmailReportForm, ColaboradorForm
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

@admin_bp.route('/escalas', methods=['GET', 'POST'])
@login_required
@admin_required
def gerenciar_escalas():
    try:
        ano_selecionado = request.args.get('ano', default=datetime.now().year, type=int)
        mes_selecionado = request.args.get('mes', default=datetime.now().month, type=int)
    except (ValueError, TypeError):
        ano_selecionado = datetime.now().year
        mes_selecionado = datetime.now().month

    turnos_definidos = ['Diurno Par', 'Diurno Impar', 'Noturno Par', 'Noturno Impar']
    
    if request.method == 'POST':
        ano_form = request.form.get('ano', type=int)
        mes_form = request.form.get('mes', type=int)
        
        # Chama o serviço para salvar os dados
        sucesso, mensagem = salvar_escala_mensal(ano_form, mes_form, request.form)
        
        if sucesso:
            flash(mensagem, 'success')
        else:
            logger.error(f"Erro ao atualizar escala de supervisores: {mensagem}")
            flash(mensagem, 'danger')
        
        return redirect(url_for('admin.gerenciar_escalas', ano=ano_form, mes=mes_form))

    # ---- Lógica para o método GET ----

    # Busca os dados através do serviço
    escalas_atuais = get_escala_mensal(ano_selecionado, mes_selecionado)
    
    # Busca dados para preencher os menus do formulário
    supervisores = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    anos_disponiveis = range(datetime.now().year - 2, datetime.now().year + 3)
    meses_disponiveis = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
        (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    return render_template('admin/gerenciar_escalas.html',
                           title='Gerenciar Escalas de Supervisores',
                           turnos=turnos_definidos,
                           supervisores=supervisores,
                           escalas_atuais=escalas_atuais,
                           anos=anos_disponiveis,
                           meses=meses_disponiveis,
                           ano_selecionado=ano_selecionado,
                           mes_selecionado=mes_selecionado)


@admin_bp.route('/ferramentas', methods=['GET'])
@login_required
@admin_required
def admin_tools():
    logger.info(f"Admin '{current_user.username}' acessou o menu de ferramentas.")
    return render_template('admin/ferramentas.html', title='Ferramentas Administrativas')


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
        if custom_greeting: parts.append(custom_greeting)
        elif include_greeting: parts.append("Prezados(as),")
        if parts: parts.append("")
        parts.append(raw_report)
        if raw_report.strip() and (custom_closing or include_closing): parts.append("")
        if custom_closing: parts.append(custom_closing)
        elif include_closing: parts.append("Atenciosamente,\nEquipe Administrativa")
        formatted_report = "\n".join(parts)
        flash('Relatório formatado para e-mail com sucesso!', 'success')
    return render_template('admin/formatar_email.html', title='Formatar Relatório para E-mail', form=form, formatted_report=formatted_report)


@admin_bp.route('/ferramentas/gerador-justificativas', methods=['GET'])
@login_required
@admin_required
def gerador_justificativas_tool():
    logger.info(f"Admin '{current_user.username}' acessou o Gerador de Justificativas.")
    return render_template('admin/gerador_justificativas.html', title='Gerador de Justificativas iFractal')


@admin_bp.route('/ferramentas/api/processar-justificativa', methods=['POST'])
@login_required
@admin_required
def api_processar_justificativa():
    payload = request.get_json()
    if not payload: return jsonify({'erro': 'Dados não fornecidos.'}), 400
    tipo_justificativa = payload.get('tipo_justificativa')
    dados_variaveis = payload.get('dados_variaveis')
    if not tipo_justificativa or not isinstance(dados_variaveis, dict): return jsonify({'erro': "Dados inválidos."}), 400
    logger.info(f"API Processar Justificativa: Tipo='{tipo_justificativa}' por '{current_user.username}'.")
    try:
        if tipo_justificativa == "atestado":
            service = _get_justificativa_atestado_service()
            texto_gerado = service.gerar_justificativa(dados_variaveis)
        elif tipo_justificativa == "troca_plantao":
            service = _get_justificativa_troca_plantao_service()
            texto_gerado = service.gerar_justificativa_troca(dados_variaveis)
        else: return jsonify({'erro': f"Tipo de justificativa desconhecido: {tipo_justificativa}"}), 400
        return jsonify({'justificativa_gerada': texto_gerado})
    except Exception as e:
        logger.error(f"API Processar Justificativa: Erro inesperado: {e}", exc_info=True)
        return jsonify({'erro': f'Erro inesperado: {str(e)}'}), 500
