from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.decorators.admin_required import admin_required
from app.middleware.user_activity import get_online_users_list, get_online_users_count
from app.models.user_online import UserOnline
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

online_users_bp = Blueprint('online_users', __name__, url_prefix='/admin/online')

@online_users_bp.route('/')
@login_required
@admin_required
def online_users_dashboard():
    """Dashboard de usuários online."""
    try:
        online_users = get_online_users_list()
        online_count = len(online_users)
        
        return render_template(
            'admin/online_users.html',
            title="Usuários Online",
            online_users=online_users,
            online_count=online_count
        )
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard de usuários online: {e}")
        return render_template(
            'admin/online_users.html',
            title="Usuários Online",
            online_users=[],
            online_count=0,
            error="Erro ao carregar dados"
        )

@online_users_bp.route('/api/online-users')
@login_required
@admin_required
def api_online_users():
    """API para obter lista de usuários online."""
    try:
        online_users = get_online_users_list()
        
        # Formata os dados para JSON
        users_data = []
        for user in online_users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'last_activity': user.last_activity.strftime('%d/%m/%Y %H:%M:%S') if user.last_activity else 'N/A'
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'count': len(users_data),
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Erro na API de usuários online: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter usuários online',
            'users': [],
            'count': 0
        }), 500

@online_users_bp.route('/api/online-count')
@login_required
@admin_required
def api_online_count():
    """API para obter apenas a contagem de usuários online."""
    try:
        count = get_online_users_count()
        return jsonify({
            'success': True,
            'count': count,
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Erro na API de contagem online: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter contagem',
            'count': 0
        }), 500

@online_users_bp.route('/api/cleanup-sessions', methods=['POST'])
@login_required
@admin_required
def api_cleanup_sessions():
    """API para limpar sessões antigas."""
    try:
        UserOnline.cleanup_old_sessions()
        return jsonify({
            'success': True,
            'message': 'Sessões antigas removidas com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao limpar sessões: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao limpar sessões'
        }), 500

@online_users_bp.route('/api/debug-sessions')
@login_required
@admin_required
def api_debug_sessions():
    """API para debug das sessões."""
    try:
        # Busca todas as sessões (não apenas as online)
        all_sessions = UserOnline.query.all()
        sessions_data = []
        
        for session in all_sessions:
            sessions_data.append({
                'id': session.id,
                'user_id': session.user_id,
                'session_id': session.session_id[:20] + '...' if len(session.session_id) > 20 else session.session_id,
                'ip_address': session.ip_address,
                'last_activity': session.last_activity.strftime('%d/%m/%Y %H:%M:%S') if session.last_activity else 'N/A',
                'created_at': session.created_at.strftime('%d/%m/%Y %H:%M:%S') if session.created_at else 'N/A'
            })
        
        return jsonify({
            'success': True,
            'total_sessions': len(sessions_data),
            'sessions': sessions_data
        })
    except Exception as e:
        logger.error(f"Erro no debug de sessões: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter debug de sessões'
        }), 500 