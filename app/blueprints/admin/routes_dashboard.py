# app/blueprints/admin/routes_dashboard.py
import logging
from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from . import admin_bp
from app import db
from app.decorators.admin_required import admin_required
from app.models import User, Condominio, LoginHistory, ProcessingHistory
from app.services.dashboard_service import get_main_dashboard_data, get_ronda_dashboard_data

logger = logging.getLogger(__name__)

# ... (as rotas 'dashboard' e 'dashboard_metrics' continuam iguais) ...
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return redirect(url_for('admin.dashboard_metrics'))


@admin_bp.route('/dashboard_metrics')
@login_required
@admin_required
def dashboard_metrics():
    logger.info(f"Admin '{current_user.username}' acessou o dashboard de métricas.")
    context_data = get_main_dashboard_data()
    context_data['title'] = 'Dashboard de Métricas'
    return render_template('admin/dashboard.html', **context_data)


@admin_bp.route('/ronda_dashboard')
@login_required
@admin_required
def ronda_dashboard():
    logger.info(f"Admin '{current_user.username}' acessou o dashboard de rondas.")
    
    filters = {
        'turno': request.args.get('turno', ''),
        'supervisor_id': request.args.get('supervisor_id', type=int),
        'condominio_id': request.args.get('condominio_id', type=int),
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
        'data_especifica': request.args.get('data_especifica', '')
    }

    context_data = get_ronda_dashboard_data(filters)

    context_data['title'] = 'Dashboard de Métricas de Rondas'
    context_data['turnos'] = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['condominios'] = Condominio.query.order_by(Condominio.nome).all()
    context_data['selected_turno'] = filters['turno']
    context_data['selected_supervisor_id'] = filters['supervisor_id']
    context_data['selected_condominio_id'] = filters['condominio_id']
    context_data['selected_data_inicio'] = filters['data_inicio_str']
    context_data['selected_data_fim'] = filters['data_fim_str']
    context_data['selected_data_especifica'] = filters['data_especifica']
    
    # --- INÍCIO DA CORREÇÃO ---
    # Formata a data aqui, no backend, antes de enviar para o template
    context_data['data_analise_formatada'] = ''
    if filters['data_especifica']:
        try:
            dt_obj = datetime.strptime(filters['data_especifica'], '%Y-%m-%d')
            context_data['data_analise_formatada'] = dt_obj.strftime('%d/%m/%Y')
        except ValueError:
            # Caso a data seja inválida, não faz nada, o serviço já deve ter tratado o erro
            pass
    # --- FIM DA CORREÇÃO ---

    return render_template('admin/ronda_dashboard.html', **context_data)