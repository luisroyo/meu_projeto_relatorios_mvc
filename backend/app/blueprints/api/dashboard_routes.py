"""
APIs de dashboard para fornecer dados para o frontend.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc

from app import db
from app.models import Ocorrencia, Ronda, User, Condominio
from app.blueprints.api.utils import success_response, error_response

dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

logger = logging.getLogger(__name__)

@dashboard_api_bp.route('/test', methods=['GET'])
@jwt_required()
def test_jwt():
    """Endpoint de teste para verificar se o JWT está funcionando."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Log para debug
    logger.info(f"JWT Test - User ID: {current_user_id}, Username: {user.username}")
    
    return jsonify({
        'success': True,
        'message': 'JWT está funcionando!',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'headers': {
            'authorization': request.headers.get('Authorization', 'Não encontrado'),
            'content_type': request.headers.get('Content-Type', 'Não encontrado')
        }
    }), 200

@dashboard_api_bp.route('/test-public', methods=['GET'])
def test_public():
    """Endpoint público de teste."""
    return jsonify({
        'success': True,
        'message': 'Endpoint público funcionando!',
        'timestamp': datetime.now().isoformat()
    }), 200

@dashboard_api_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Obter estatísticas gerais do dashboard."""
    try:
        # Estatísticas de ocorrências
        total_ocorrencias = Ocorrencia.query.count()
        ocorrencias_hoje = Ocorrencia.query.filter(
            func.date(Ocorrencia.data_hora_ocorrencia) == datetime.now().date()
        ).count()
        
        # Estatísticas de rondas
        total_rondas = Ronda.query.count()
        rondas_hoje = Ronda.query.filter(
            func.date(Ronda.data_plantao_ronda) == datetime.now().date()
        ).count()
        
        # Estatísticas de usuários
        total_usuarios = User.query.filter_by(is_approved=True).count()
        usuarios_online = User.query.filter(
            User.last_login >= datetime.now() - timedelta(hours=1)
        ).count()
        
        # Estatísticas de condomínios
        total_condominios = Condominio.query.count()
        
        # Get current user for the response
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Calculate stats for the last month
        last_month = datetime.now() - timedelta(days=30)
        ocorrencias_ultimo_mes = Ocorrencia.query.filter(Ocorrencia.data_hora_ocorrencia >= last_month).count()
        rondas_ultimo_mes = Ronda.query.filter(Ronda.data_plantao_ronda >= last_month).count()
        rondas_em_andamento = Ronda.query.filter(Ronda.status == 'Em Andamento').count()

        stats = {
            'stats': {
                'total_ocorrencias': total_ocorrencias,
                'total_rondas': total_rondas,
                'total_condominios': total_condominios,
                'rondas_em_andamento': rondas_em_andamento,
                'ocorrencias_ultimo_mes': ocorrencias_ultimo_mes,
                'rondas_ultimo_mes': rondas_ultimo_mes
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin,
                'is_supervisor': user.is_supervisor
            } if user else None
        }
        
        return success_response(
            data=stats,
            message='Estatísticas obtidas com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do dashboard: {e}")
        return error_response('Erro interno ao obter estatísticas', status_code=500)

@dashboard_api_bp.route('/recent-ocorrencias', methods=['GET'])
@jwt_required()
def get_recent_ocorrencias():
    """Obter ocorrências recentes."""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        ocorrencias = Ocorrencia.query.options(
            db.joinedload(Ocorrencia.tipo),
            db.joinedload(Ocorrencia.condominio),
            db.joinedload(Ocorrencia.supervisor)
        ).order_by(desc(Ocorrencia.data_hora_ocorrencia)).limit(limit).all()
        
        ocorrencias_data = []
        for o in ocorrencias:
            ocorrencias_data.append({
                'id': o.id,
                'tipo': o.tipo.nome if o.tipo else 'N/A',
                'condominio': o.condominio.nome if o.condominio else 'N/A',
                'data': o.data_hora_ocorrencia.isoformat() if o.data_hora_ocorrencia else None,
                'descricao': o.relatorio_final or 'Sem descrição',
                'status': o.status,
                'turno': o.turno,
                'supervisor': o.supervisor.username if o.supervisor else 'N/A'
            })
        
        return success_response(
            data={'ocorrencias': ocorrencias_data},
            message='Ocorrências recentes obtidas com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter ocorrências recentes: {e}")
        return error_response('Erro interno ao obter ocorrências recentes', status_code=500)

@dashboard_api_bp.route('/recent-rondas', methods=['GET'])
@jwt_required()
def get_recent_rondas():
    """Obter rondas recentes."""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        rondas = Ronda.query.options(
            db.joinedload(Ronda.condominio),
            db.joinedload(Ronda.supervisor)
        ).order_by(desc(Ronda.data_plantao_ronda)).limit(limit).all()
        
        rondas_data = []
        for r in rondas:
            rondas_data.append({
                'id': r.id,
                'condominio': r.condominio.nome if r.condominio else 'N/A',
                'data_plantao': r.data_plantao_ronda.isoformat() if r.data_plantao_ronda else None,
                'escala_plantao': r.escala_plantao,
                'status': r.status,
                'total_rondas': r.total_rondas_no_log or 0,
                'supervisor': r.supervisor.username if r.supervisor else 'N/A'
            })
        
        return success_response(
            data={'rondas': rondas_data},
            message='Rondas recentes obtidas com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter rondas recentes: {e}")
        return error_response('Erro interno ao obter rondas recentes', status_code=500)

@dashboard_api_bp.route('/chart-data', methods=['GET'])
@jwt_required()
def get_chart_data():
    """Obter dados para gráficos do dashboard."""
    try:
        # Dados dos últimos 7 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Ocorrências por dia
        ocorrencias_por_dia = db.session.query(
            func.date(Ocorrencia.data_hora_ocorrencia).label('data'),
            func.count(Ocorrencia.id).label('total')
        ).filter(
            Ocorrencia.data_hora_ocorrencia.between(start_date, end_date)
        ).group_by(
            func.date(Ocorrencia.data_hora_ocorrencia)
        ).all()
        
        # Rondas por dia
        rondas_por_dia = db.session.query(
            func.date(Ronda.data_plantao_ronda).label('data'),
            func.count(Ronda.id).label('total')
        ).filter(
            Ronda.data_plantao_ronda.between(start_date, end_date)
        ).group_by(
            func.date(Ronda.data_plantao_ronda)
        ).all()
        
        chart_data = {
            'ocorrencias_por_dia': [
                {'data': str(item.data), 'total': item.total} 
                for item in ocorrencias_por_dia
            ],
            'rondas_por_dia': [
                {'data': str(item.data), 'total': item.total} 
                for item in rondas_por_dia
            ]
        }
        
        return success_response(
            data=chart_data,
            message='Dados dos gráficos obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter dados dos gráficos: {e}")
        return error_response('Erro interno ao obter dados dos gráficos', status_code=500) 