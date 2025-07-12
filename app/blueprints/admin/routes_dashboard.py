# app/blueprints/admin/routes_dashboard.py
import logging
from flask import flash, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
import locale

from . import admin_bp
from app import db
from app.decorators.admin_required import admin_required
from app.models import User, Condominio, Ronda, Ocorrencia, OcorrenciaTipo
from app.services.dashboard_service import get_main_dashboard_data, get_ronda_dashboard_data, get_ocorrencia_dashboard_data

logger = logging.getLogger(__name__)

# --- Funções Auxiliares ---

def _setup_locale():
    """Tenta configurar o locale para pt_BR para nomes de meses em português."""
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR')
        except locale.Error:
            logger.warning("Locale 'pt_BR' não encontrado. Nomes de meses podem aparecer em inglês.")

_setup_locale()

def _get_date_range_from_month(year, month):
    """Calcula e formata as datas de início e fim para um determinado mês e ano."""
    if not month or not 1 <= month <= 12:
        return None, None
    try:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    except ValueError:
        return None, None

def _get_period_description(year, month, start_date_str, end_date_str):
    """Gera uma descrição amigável para o período de tempo selecionado."""
    def get_month_name(y, m):
        try:
            return datetime(y, m, 1).strftime('%B').capitalize()
        except Exception:
            return datetime(y, m, 1).strftime('%B')

    if month:
        month_name = get_month_name(year, month)
        return f"Referente a {month_name} de {year}"
    elif start_date_str and end_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            return f"Período de {start_dt.strftime('%d/%m/%Y')} a {end_dt.strftime('%d/%m/%Y')}"
        except ValueError:
             return "Período de data personalizado"
    else:
        now = datetime.now()
        month_name = get_month_name(now.year, now.month)
        return f"Referente a {month_name} de {now.year}"

def _get_months_of_year(year):
    """Retorna uma lista de dicionários com os meses do ano para filtros."""
    meses = []
    for i in range(1, 13):
        try:
            mes_nome = datetime(year, i, 1).strftime('%B').capitalize()
        except Exception:
            mes_nome = datetime(year, i, 1).strftime('%B')
        meses.append({'id': i, 'nome': mes_nome})
    return meses

# --- Rotas do Dashboard ---

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Rota principal do painel admin, redireciona para as métricas gerais."""
    return redirect(url_for('admin.dashboard_metrics'))

@admin_bp.route('/dashboard_metrics')
@login_required
@admin_required
def dashboard_metrics():
    """Exibe o dashboard com métricas gerais do sistema."""
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de métricas.")
    context_data = get_main_dashboard_data()
    context_data['title'] = 'Dashboard de Métricas Gerais'
    return render_template('admin/dashboard.html', **context_data)

@admin_bp.route('/ronda_dashboard')
@login_required
@admin_required
def ronda_dashboard():
    """Exibe o dashboard de métricas e análises de Rondas."""
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
    if filters['mes'] and not (filters['data_inicio_str'] or filters['data_fim_str']):
        start_date, end_date = _get_date_range_from_month(current_year, filters['mes'])
        if start_date and end_date:
            filters['data_inicio_str'] = start_date
            filters['data_fim_str'] = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            filters['mes'] = None

    context_data = get_ronda_dashboard_data(filters)
    
    context_data['title'] = 'Dashboard de Métricas de Rondas'
    context_data['turnos'] = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['condominios'] = Condominio.query.join(Ronda).distinct().order_by(Condominio.nome).all()
    context_data['meses_do_ano'] = _get_months_of_year(current_year)
    
    context_data['selected_filters'] = filters
    
    context_data['period_description'] = _get_period_description(
        current_year, filters['mes'], filters['data_inicio_str'], filters['data_fim_str']
    )
    
    return render_template('admin/ronda_dashboard.html', **context_data)

@admin_bp.route('/ocorrencia_dashboard')
@login_required
@admin_required
def ocorrencia_dashboard():
    """Exibe o dashboard de métricas e análises de Ocorrências."""
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
    if filters['mes'] and not (filters['data_inicio_str'] or filters['data_fim_str']):
        start_date, end_date = _get_date_range_from_month(current_year, filters['mes'])
        if start_date and end_date:
            filters['data_inicio_str'] = start_date
            filters['data_fim_str'] = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            filters['mes'] = None

    context_data = get_ocorrencia_dashboard_data(filters)

    context_data['title'] = 'Dashboard de Ocorrências'
    context_data['condominios'] = Condominio.query.order_by(Condominio.nome).all()
    context_data['tipos_ocorrencia'] = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['status_list'] = ['Registrada', 'Em Andamento', 'Concluída', 'Cancelada']
    context_data['meses_do_ano'] = _get_months_of_year(current_year)

    # --- INÍCIO DA CORREÇÃO ---
    context_data['selected_condominio_id'] = filters.get('condominio_id')
    context_data['selected_tipo_id'] = filters.get('tipo_id')
    context_data['selected_status'] = filters.get('status')
    context_data['selected_supervisor_id'] = filters.get('supervisor_id')
    context_data['selected_mes'] = filters.get('mes')
    context_data['selected_data_inicio_str'] = filters.get('data_inicio_str')
    context_data['selected_data_fim_str'] = filters.get('data_fim_str')
    
    context_data['period_description'] = _get_period_description(
        current_year, filters.get('mes'), filters.get('data_inicio_str'), filters.get('data_fim_str')
    )

    # Lógica para o KPI do supervisor.
    kpi_supervisor_label = ""
    kpi_supervisor_name = None
    selected_supervisor_id = filters.get('supervisor_id')

    if selected_supervisor_id:
        # Se um supervisor for selecionado, busca o nome dele.
        kpi_supervisor_label = "Supervisor Selecionado"
        supervisor = User.query.get(selected_supervisor_id)
        kpi_supervisor_name = supervisor.username if supervisor else 'N/A'
    else:
        # Se nenhum supervisor for selecionado, calcula o com mais ocorrências.
        kpi_supervisor_label = "Supervisor com Mais Ocorrências"
        try:
            query = db.session.query(
                Ocorrencia.supervisor_id,
                func.count(Ocorrencia.id).label('ocorrencia_count')
            ).join(
                User, Ocorrencia.supervisor_id == User.id
            ).filter(
                User.is_supervisor == True,
                Ocorrencia.supervisor_id != None
            )

            # Aplica os mesmos filtros da página à query do KPI
            if filters.get('condominio_id'):
                query = query.filter(Ocorrencia.condominio_id == filters['condominio_id'])
            if filters.get('tipo_id'):
                query = query.filter(Ocorrencia.tipo_id == filters['tipo_id'])
            if filters.get('status'):
                query = query.filter(Ocorrencia.status == filters['status'])

            start_date_str = filters.get('data_inicio_str')
            end_date_str = filters.get('data_fim_str')

            if start_date_str:
                query = query.filter(Ocorrencia.data_hora_ocorrencia >= datetime.strptime(start_date_str, '%Y-%m-%d'))
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Ocorrencia.data_hora_ocorrencia < end_date)

            top_supervisor_data = query.group_by(Ocorrencia.supervisor_id).order_by(func.count(Ocorrencia.id).desc()).first()
            
            if top_supervisor_data:
                supervisor = User.query.get(top_supervisor_data.supervisor_id)
                if supervisor:
                    kpi_supervisor_name = supervisor.username
            
        except Exception as e:
            logger.error(f"Erro ao calcular o supervisor com mais ocorrências: {e}")
            kpi_supervisor_name = None
    
    context_data['kpi_supervisor_label'] = kpi_supervisor_label
    context_data['kpi_supervisor_name'] = kpi_supervisor_name
    # --- FIM DA CORREÇÃO ---

    return render_template('admin/ocorrencia_dashboard.html', **context_data)
