# app/blueprints/admin/routes_dashboard.py
import logging
from flask import flash, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
import locale # Import locale for month name
from app.utils.date_utils import parse_date_range

from . import admin_bp
from app import db
from app.decorators.admin_required import admin_required
from app.models import User, Condominio, LoginHistory, ProcessingHistory, Ronda, Ocorrencia, OcorrenciaTipo
from app.services.dashboard_service import get_main_dashboard_data, get_ronda_dashboard_data, get_ocorrencia_dashboard_data

logger = logging.getLogger(__name__)

# --- BLOCO CORRIGIDO ---
# Tenta definir o locale para Português do Brasil de forma segura.
try:
    # Tenta o padrão mais comum e completo primeiro.
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        # Tenta um padrão alternativo.
        locale.setlocale(locale.LC_TIME, 'pt_BR')
    except locale.Error:
        # Se ambos falharem (comum em servidores), imprime um aviso simples no console
        # durante a inicialização e continua a execução normalmente.
        print("Aviso: Locale 'pt_BR' não está instalado no sistema. Nomes de meses podem aparecer em inglês.")
        pass # Evita que a aplicação gere um log de warning.


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """ Rota principal do painel admin, redireciona para as métricas gerais. """
    return redirect(url_for('admin.dashboard_metrics'))


@admin_bp.route('/dashboard_metrics')
@login_required
def dashboard_metrics():
    """ Exibe o dashboard com métricas gerais do sistema. """
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de métricas.")
    context_data = get_main_dashboard_data()
    context_data['title'] = 'Dashboard de Métricas Gerais'
    return render_template('admin/dashboard.html', **context_data)


@admin_bp.route('/ronda_dashboard')
@login_required
def ronda_dashboard():
    """ Exibe o dashboard de métricas e análises de Rondas. """
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de rondas.")
    
    filters = {
        'turno': request.args.get('turno', ''),
        'supervisor_id': request.args.get('supervisor_id', type=int),
        'condominio_id': request.args.get('condominio_id', type=int),
        'mes': request.args.get('mes', type=int),
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
        'data_especifica': request.args.get('data_especifica', '')
    }

    current_year = datetime.now().year
    if filters['mes']:
        try:
            filters['data_inicio_str'] = datetime(current_year, filters['mes'], 1).strftime('%Y-%m-%d')
            if filters['mes'] == 12:
                filters['data_fim_str'] = datetime(current_year, 12, 31).strftime('%Y-%m-%d')
            else:
                filters['data_fim_str'] = (datetime(current_year, filters['mes'] + 1, 1) - timedelta(days=1)).strftime('%Y-%m-%d')
        except ValueError:
            flash("Mês inválido selecionado.", "danger")
            filters['mes'] = None

    context_data = get_ronda_dashboard_data(filters)
    context_data['title'] = 'Dashboard de Métricas de Rondas'
    context_data['turnos'] = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['condominios'] = Condominio.query.join(Ronda).distinct().order_by(Condominio.nome).all()
    
    meses_do_ano = []
    for i in range(1, 13):
        mes_nome = datetime(current_year, i, 1).strftime('%B').capitalize()
        meses_do_ano.append({'id': i, 'nome': mes_nome})
    context_data['meses_do_ano'] = meses_do_ano
    context_data['selected_mes'] = filters['mes']

    context_data['selected_data_inicio_str'] = filters['data_inicio_str']
    context_data['selected_data_fim_str'] = filters['data_fim_str']
    context_data.update({f'selected_{key}': val for key, val in filters.items()})

    if filters['mes']:
        mes_nome_selecionado = datetime(current_year, filters['mes'], 1).strftime('%B').capitalize()
        context_data['current_month_description'] = f"Referente a {mes_nome_selecionado} de {current_year}"
    elif not filters['data_inicio_str'] and not filters['data_fim_str']:
        current_date_for_display = datetime.now()
        current_month_name = current_date_for_display.strftime('%B').capitalize()
        current_year_display = current_date_for_display.year
        context_data['current_month_description'] = f"Referente a {current_month_name} de {current_year_display}"
    else:
        context_data['current_month_description'] = ""
    
    return render_template('admin/ronda_dashboard.html', **context_data)


@admin_bp.route('/ocorrencia_dashboard')
@login_required
def ocorrencia_dashboard():
    """ Exibe o dashboard de métricas e análises de Ocorrências. """
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de ocorrências.")

    filters = {
        'condominio_id': request.args.get('condominio_id', type=int),
        'tipo_id': request.args.get('tipo_id', type=int),
        'status': request.args.get('status', ''),
        'supervisor_id': request.args.get('supervisor_id', type=int),
        'mes': request.args.get('mes', type=int),
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
    }

    current_year = datetime.now().year
    if filters['mes']:
        try:
            filters['data_inicio_str'] = datetime(current_year, filters['mes'], 1).strftime('%Y-%m-%d')
            if filters['mes'] == 12:
                filters['data_fim_str'] = datetime(current_year, 12, 31).strftime('%Y-%m-%d')
            else:
                filters['data_fim_str'] = (datetime(current_year, filters['mes'] + 1, 1) - timedelta(days=1)).strftime('%Y-%m-%d')
        except ValueError:
            flash("Mês inválido selecionado.", "danger")
            filters['mes'] = None

    context_data = get_ocorrencia_dashboard_data(filters)
    context_data['title'] = 'Dashboard de Ocorrências'
    context_data['condominios'] = Condominio.query.order_by(Condominio.nome).all()
    context_data['tipos_ocorrencia'] = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['status_list'] = ['Registrada', 'Em Andamento', 'Concluída', 'Cancelada']

    meses_do_ano = []
    for i in range(1, 13):
        mes_nome = datetime(current_year, i, 1).strftime('%B').capitalize()
        meses_do_ano.append({'id': i, 'nome': mes_nome})
    context_data['meses_do_ano'] = meses_do_ano
    
    context_data['selected_data_inicio_str'] = filters['data_inicio_str']
    context_data['selected_data_fim_str'] = filters['data_fim_str']
    context_data['selected_mes'] = filters['mes']

    if filters['mes']:
        mes_nome_selecionado = datetime(current_year, filters['mes'], 1).strftime('%B').capitalize()
        context_data['current_month_description'] = f"Referente a {mes_nome_selecionado} de {current_year}"
    elif not filters['data_inicio_str'] and not filters['data_fim_str']:
        current_date_for_display = datetime.now()
        current_month_name = current_date_for_display.strftime('%B').capitalize()
        current_year_display = current_date_for_display.year
        context_data['current_month_description'] = f"Referente a {current_month_name} de {current_year_display}"
    else:
        context_data['current_month_description'] = ""

    return render_template('admin/ocorrencia_dashboard.html', **context_data)