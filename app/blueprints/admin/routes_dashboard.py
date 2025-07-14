# app/blueprints/admin/routes_dashboard.py
import logging
import locale
from flask import flash, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app.decorators.admin_required import admin_required
from app.services.dashboard.comparativo_dashboard import get_monthly_comparison_data
from app.services.dashboard.main_dashboard import get_main_dashboard_data
from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data

from . import admin_bp
from app.models import User, Condominio, Ronda, Ocorrencia, OcorrenciaTipo
from app.services.dashboard import get_ronda_dashboard_data
## [MELHORIA] Importando Enums para popular os filtros do formulário.
from app.constants import Turnos, OcorrenciaStatus

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
            # Fallback para o nome do mês padrão do sistema
            return datetime(y, m, 1).strftime('%B')

    if month and year:
        month_name = get_month_name(year, month)
        return f"Referente a {month_name} de {year}"
    elif start_date_str and end_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_dt == end_dt:
                return f"Referente ao dia {start_dt.strftime('%d/%m/%Y')}"
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
    
    current_year = datetime.now().year
    
    filters = {
        'turno': request.args.get('turno', ''),
        'supervisor_id': request.args.get('supervisor_id', type=int),
        'condominio_id': request.args.get('condominio_id', type=int),
        'mes': request.args.get('mes', type=int),
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
        'data_especifica': request.args.get('data_especifica', '')
    }

    if filters['mes'] and not (filters['data_inicio_str'] or filters['data_fim_str']):
        start_date, end_date = _get_date_range_from_month(current_year, filters['mes'])
        if start_date and end_date:
            filters['data_inicio_str'] = start_date
            filters['data_fim_str'] = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            filters['mes'] = None

    context_data = get_ronda_dashboard_data(filters)
    
    # --- Preenchendo dados para os filtros do template ---
    context_data['title'] = 'Dashboard de Métricas de Rondas'
    ## [MELHORIA] Usando o Enum de Turnos para popular a lista do filtro.
    context_data['turnos'] = [turno.value for turno in Turnos]
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['condominios'] = Condominio.query.join(Ronda).distinct().order_by(Condominio.nome).all()
    context_data['meses_do_ano'] = _get_months_of_year(current_year)
    
    context_data['selected_filters'] = filters
    
    context_data['period_description'] = _get_period_description(
        current_year, filters['mes'], context_data['selected_data_inicio_str'], context_data['selected_data_fim_str']
    )
    
    return render_template('admin/ronda_dashboard.html', **context_data)

@admin_bp.route('/ocorrencia_dashboard')
@login_required
@admin_required
def ocorrencia_dashboard():
    """Exibe o dashboard de métricas e análises de Ocorrências."""
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard de ocorrências.")

    current_year = datetime.now().year

    filters = {
        'condominio_id': request.args.get('condominio_id', type=int),
        'tipo_id': request.args.get('tipo_id', type=int),
        'status': request.args.get('status', ''),
        'supervisor_id': request.args.get('supervisor_id', type=int),
        'mes': request.args.get('mes', type=int),
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
    }

    if filters['mes'] and not (filters['data_inicio_str'] or filters['data_fim_str']):
        start_date, end_date = _get_date_range_from_month(current_year, filters['mes'])
        if start_date and end_date:
            filters['data_inicio_str'] = start_date
            filters['data_fim_str'] = end_date
        else:
            flash("Mês inválido selecionado.", "danger")
            filters['mes'] = None

    ## [MELHORIA CRÍTICA] A rota agora apenas chama o serviço e passa os dados.
    # Toda a lógica de cálculo de KPIs foi movida para dashboard_service.py.
    context_data = get_ocorrencia_dashboard_data(filters)

    # --- Preenchendo dados para os filtros do template ---
    context_data['title'] = 'Dashboard de Ocorrências'
    context_data['condominios'] = Condominio.query.order_by(Condominio.nome).all()
    context_data['tipos_ocorrencia'] = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    ## [MELHORIA] Usando Enum para popular a lista de status.
    context_data['status_list'] = [status.value for status in OcorrenciaStatus]
    context_data['meses_do_ano'] = _get_months_of_year(current_year)

    ## [MELHORIA] Passando o dicionário de filtros diretamente para o template.
    # Isso simplifica o código e evita atribuições manuais e repetitivas.
    context_data['selected_filters'] = filters
    
    context_data['period_description'] = _get_period_description(
        current_year, filters.get('mes'), context_data['selected_data_inicio_str'], context_data['selected_data_fim_str']
    )

    # A rota agora está muito mais limpa e focada em sua responsabilidade.
    return render_template('admin/ocorrencia_dashboard.html', **context_data)

# --- [NOVO] Rota para o Dashboard Comparativo ---
@admin_bp.route('/dashboard/comparativo')
@login_required
@admin_required
def dashboard_comparativo():
    """Exibe a página de análise mensal comparativa de rondas e ocorrências."""
    logger.info(f"Usuário '{current_user.username}' acessou o dashboard comparativo.")
    
    # Pega o ano do parâmetro da URL, ou usa o ano atual como padrão
    year = request.args.get('year', default=datetime.now().year, type=int)
    
    # Busca os dados processados pelo novo serviço
    data = get_monthly_comparison_data(year)
    
    # Adiciona o título e renderiza o novo template com os dados
    data['title'] = 'Análise Mensal Comparativa'
    return render_template('admin/dashboard_comparativo.html', **data)