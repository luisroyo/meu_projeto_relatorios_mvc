"""
APIs de dashboard para fornecer dados para o frontend.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.ocorrencia import Ocorrencia
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

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
    """Obter estatísticas do dashboard."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        # Estatísticas gerais
        total_ocorrencias = Ocorrencia.query.count()
        total_rondas = RondaEsporadica.query.count()
        total_condominios = Condominio.query.count()
        
        # Rondas em andamento hoje
        hoje = datetime.now().date()
        rondas_em_andamento = RondaEsporadica.query.filter(
            RondaEsporadica.data_plantao == hoje,
            RondaEsporadica.status == 'em_andamento'
        ).count()
        
        # Ocorrências do último mês
        um_mes_atras = datetime.now() - timedelta(days=30)
        ocorrencias_ultimo_mes = Ocorrencia.query.filter(
            Ocorrencia.data_hora_ocorrencia >= um_mes_atras
        ).count()
        
        # Rondas do último mês
        rondas_ultimo_mes = RondaEsporadica.query.filter(
            RondaEsporadica.data_plantao >= um_mes_atras
        ).count()
        
        return jsonify({
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
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do dashboard: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dashboard_api_bp.route('/recent-ocorrencias', methods=['GET'])
@jwt_required()
def get_recent_ocorrencias():
    """Obter ocorrências recentes."""
    try:
        ocorrencias = Ocorrencia.query.order_by(
            Ocorrencia.data_hora_ocorrencia.desc()
        ).limit(10).all()
        
        return jsonify({
            'ocorrencias': [{
                'id': o.id,
                'tipo': o.tipo.nome if o.tipo else 'N/A',
                'condominio': o.condominio.nome if o.condominio else 'N/A',
                'data': o.data_hora_ocorrencia.isoformat() if o.data_hora_ocorrencia else None,
                'descricao': o.relatorio_final[:100] + '...' if len(o.relatorio_final) > 100 else o.relatorio_final
            } for o in ocorrencias]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ocorrências recentes: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dashboard_api_bp.route('/recent-rondas', methods=['GET'])
@jwt_required()
def get_recent_rondas():
    """Obter rondas recentes."""
    try:
        rondas = RondaEsporadica.query.order_by(
            RondaEsporadica.data_plantao.desc()
        ).limit(10).all()
        
        return jsonify({
            'rondas': [{
                'id': r.id,
                'condominio': r.condominio.nome if r.condominio else 'N/A',
                'data_plantao': r.data_plantao.isoformat() if r.data_plantao else None,
                'escala_plantao': r.escala_plantao,
                'status': r.status,
                'total_rondas': r.total_rondas
            } for r in rondas]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter rondas recentes: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dashboard_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def get_condominios():
    """Obter lista de condomínios."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        return jsonify({
            'condominios': [{
                'id': c.id,
                'nome': c.nome
            } for c in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter condomínios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500 