from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import logging

from app.models.gemini_usage import GeminiUsageLog
from app.models.user import User
from app import db

# Blueprint para o dashboard do Gemini
gemini_dashboard_bp = Blueprint('gemini_dashboard', __name__, url_prefix='/admin/gemini-dashboard')

logger = logging.getLogger(__name__)

@gemini_dashboard_bp.route('/')
@login_required
def dashboard():
    """Dashboard principal de monitoramento do Gemini."""
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    
    # Filtros
    days = request.args.get('days', 7, type=int)
    api_key = request.args.get('api_key', 'all')
    service = request.args.get('service', 'all')
    user_id = request.args.get('user_id', 'all')
    
    # Data de início
    start_date = datetime.now() - timedelta(days=days)
    
    # Query base
    query = GeminiUsageLog.query.filter(GeminiUsageLog.created_at >= start_date)
    
    # Aplicar filtros
    if api_key != 'all':
        query = query.filter(GeminiUsageLog.api_key_name == api_key)
    if service != 'all':
        query = query.filter(GeminiUsageLog.service_name == service)
    if user_id != 'all':
        query = query.filter(GeminiUsageLog.user_id == user_id)
    
    # Estatísticas gerais
    total_requests = query.count()
    successful_requests = query.filter(GeminiUsageLog.success == True).count()
    failed_requests = query.filter(GeminiUsageLog.success == False).count()
    cache_hits = query.filter(GeminiUsageLog.cache_hit == True).count()
    
    # Uso por API key (simplificado)
    api_key_usage = db.session.query(
        GeminiUsageLog.api_key_name,
        func.count(GeminiUsageLog.id).label('count')
    ).filter(GeminiUsageLog.created_at >= start_date).group_by(GeminiUsageLog.api_key_name).all()
    
    # Uso por usuário (simplificado)
    user_usage = db.session.query(
        GeminiUsageLog.username,
        func.count(GeminiUsageLog.id).label('count')
    ).filter(GeminiUsageLog.created_at >= start_date).group_by(GeminiUsageLog.username).order_by(desc('count')).limit(10).all()
    
    # Uso por serviço
    service_usage = db.session.query(
        GeminiUsageLog.service_name,
        func.count(GeminiUsageLog.id).label('count')
    ).filter(GeminiUsageLog.created_at >= start_date).group_by(GeminiUsageLog.service_name).all()
    
    # Uso por hora (últimas 24h) - simplificado para SQLite
    hourly_usage = []
    for i in range(24):
        hour_start = datetime.now() - timedelta(hours=i+1)
        hour_end = datetime.now() - timedelta(hours=i)
        count = GeminiUsageLog.query.filter(
            and_(GeminiUsageLog.created_at >= hour_start, GeminiUsageLog.created_at < hour_end)
        ).count()
        hourly_usage.append({
            'hour': hour_start.strftime('%H:00'),
            'count': count
        })
    hourly_usage.reverse()  # Ordenar do mais antigo para o mais recente
    
    # Requisições recentes
    recent_requests = query.order_by(desc(GeminiUsageLog.created_at)).limit(20).all()
    
    # Opções para filtros
    api_keys = db.session.query(GeminiUsageLog.api_key_name).distinct().all()
    services = db.session.query(GeminiUsageLog.service_name).distinct().all()
    users = db.session.query(GeminiUsageLog.username).distinct().filter(GeminiUsageLog.username.isnot(None)).all()
    
    return render_template('admin/gemini_dashboard.html',
                         total_requests=total_requests,
                         successful_requests=successful_requests,
                         failed_requests=failed_requests,
                         cache_hits=cache_hits,
                         api_key_usage=api_key_usage,
                         user_usage=user_usage,
                         service_usage=service_usage,
                         hourly_usage=hourly_usage,
                         recent_requests=recent_requests,
                         api_keys=api_keys,
                         services=services,
                         users=users,
                         days=days,
                         selected_api_key=api_key,
                         selected_service=service,
                         selected_user=user_id)

@gemini_dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API para obter estatísticas em tempo real."""
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # Estatísticas gerais
    total_requests = GeminiUsageLog.query.filter(GeminiUsageLog.created_at >= start_date).count()
    successful_requests = GeminiUsageLog.query.filter(
        and_(GeminiUsageLog.created_at >= start_date, GeminiUsageLog.success == True)
    ).count()
    cache_hits = GeminiUsageLog.query.filter(
        and_(GeminiUsageLog.created_at >= start_date, GeminiUsageLog.cache_hit == True)
    ).count()
    
    # Uso por API key
    api_key_usage = db.session.query(
        GeminiUsageLog.api_key_name,
        func.count(GeminiUsageLog.id).label('count')
    ).filter(GeminiUsageLog.created_at >= start_date).group_by(GeminiUsageLog.api_key_name).all()
    
    return jsonify({
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'cache_hits': cache_hits,
        'api_key_usage': [{'name': item[0], 'count': item[1]} for item in api_key_usage]
    })

@gemini_dashboard_bp.route('/api/recent-requests')
@login_required
def api_recent_requests():
    """API para obter requisições recentes."""
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    limit = request.args.get('limit', 20, type=int)
    recent_requests = GeminiUsageLog.query.order_by(desc(GeminiUsageLog.created_at)).limit(limit).all()
    
    return jsonify({
        'requests': [{
            'id': req.id,
            'username': req.username or 'Anônimo',
            'api_key_name': req.api_key_name,
            'service_name': req.service_name,
            'success': req.success,
            'cache_hit': req.cache_hit,
            'prompt_length': req.prompt_length,
            'response_length': req.response_length,
            'created_at': req.created_at.isoformat(),
            'ip_address': req.ip_address
        } for req in recent_requests]
    })

@gemini_dashboard_bp.route('/api/user-details/<int:user_id>')
@login_required
def api_user_details(user_id):
    """API para obter detalhes de uso de um usuário específico."""
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    user_requests = GeminiUsageLog.query.filter(
        and_(GeminiUsageLog.user_id == user_id, GeminiUsageLog.created_at >= start_date)
    ).order_by(desc(GeminiUsageLog.created_at)).all()
    
    total_requests = len(user_requests)
    successful_requests = sum(1 for req in user_requests if req.success)
    cache_hits = sum(1 for req in user_requests if req.cache_hit)
    
    return jsonify({
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'cache_hits': cache_hits,
        'requests': [{
            'id': req.id,
            'api_key_name': req.api_key_name,
            'service_name': req.service_name,
            'success': req.success,
            'cache_hit': req.cache_hit,
            'created_at': req.created_at.isoformat(),
            'error_message': req.error_message
        } for req in user_requests]
    }) 