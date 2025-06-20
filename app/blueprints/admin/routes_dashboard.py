# app/blueprints/admin/routes_dashboard.py
import logging
from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from app.services.dashboard_service import get_main_dashboard_data

from . import admin_bp
from app import db
from app.decorators.admin_required import admin_required
from app.models import User, Condominio, LoginHistory, ProcessingHistory
from app.services.dashboard_service import get_ronda_dashboard_data # <-- IMPORTA NOSSO SERVIÇO

logger = logging.getLogger(__name__)

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

    # 1. Chama o serviço que faz todo o trabalho
    context_data = get_main_dashboard_data()
    context_data['title'] = 'Dashboard de Métricas'
    
    # 2. Renderiza o template com os dados
    return render_template('admin/dashboard.html', **context_data)

@admin_bp.route('/ronda_dashboard')
@login_required
@admin_required
def ronda_dashboard():
    logger.info(f"Admin '{current_user.username}' acessou o dashboard de rondas.")
    
    # 1. Coleta os filtros da URL da requisição
    filters = {
        'turno': request.args.get('turno', ''),
        'supervisor_id': request.args.get('supervisor_id', type=int),
        'condominio_id': request.args.get('condominio_id', type=int),
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', '')
    }

    # 2. Chama o serviço, que faz todo o trabalho pesado
    context_data = get_ronda_dashboard_data(filters)

    # 3. Adiciona ao contexto os dados para os menus de filtro do template
    context_data['title'] = 'Dashboard de Métricas de Rondas'
    context_data['turnos'] = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['condominios'] = Condominio.query.order_by(Condominio.nome).all()
    context_data['selected_turno'] = filters['turno']
    context_data['selected_supervisor_id'] = filters['supervisor_id']
    context_data['selected_condominio_id'] = filters['condominio_id']
    context_data['selected_data_inicio'] = filters['data_inicio_str']
    context_data['selected_data_fim'] = filters['data_fim_str']

    # 4. Renderiza o template, passando todo o dicionário de contexto
    return render_template('admin/ronda_dashboard.html', **context_data)