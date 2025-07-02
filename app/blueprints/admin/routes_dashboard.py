# app/blueprints/admin/routes_dashboard.py
import logging
from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

from . import admin_bp
from app import db
from app.decorators.admin_required import admin_required
from app.models import User, Condominio, LoginHistory, ProcessingHistory, Ronda, Ocorrencia, OcorrenciaTipo
from app.services.dashboard_service import get_main_dashboard_data, get_ronda_dashboard_data, get_ocorrencia_dashboard_data

logger = logging.getLogger(__name__)


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
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
        'data_especifica': request.args.get('data_especifica', '')
    }

    context_data = get_ronda_dashboard_data(filters)
    context_data['title'] = 'Dashboard de Métricas de Rondas'
    context_data['turnos'] = ['Diurno Par', 'Noturno Par', 'Diurno Impar', 'Noturno Impar']
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
    context_data['condominios'] = Condominio.query.join(Ronda).distinct().order_by(Condominio.nome).all()
    context_data.update({f'selected_{key}': val for key, val in filters.items()})
    
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
        'supervisor_id': request.args.get('supervisor_id', type=int), # NOVO FILTRO
        'data_inicio_str': request.args.get('data_inicio', ''),
        'data_fim_str': request.args.get('data_fim', ''),
    }

    context_data = get_ocorrencia_dashboard_data(filters)
    context_data['title'] = 'Dashboard de Ocorrências'
    context_data['condominios'] = Condominio.query.order_by(Condominio.nome).all()
    context_data['tipos_ocorrencia'] = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
    context_data['supervisors'] = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all() # NOVO DADO
    context_data['status_list'] = ['Registrada', 'Em Andamento', 'Concluída', 'Cancelada'] # Corrigido 'Abertta'

    context_data.update({f'selected_{key}': val for key, val in filters.items()})

    return render_template('admin/ocorrencia_dashboard.html', **context_data)
