"""
APIs de dashboard para fornecer dados para o frontend.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc

from app import db, cache
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
@cache.cached(timeout=300, key_prefix='dashboard_stats')
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


@dashboard_api_bp.route('/comparativo', methods=['GET'])
@jwt_required()
def get_dashboard_comparativo():
    """Obter dados comparativos de Rondas, Paradas e Ocorrências."""
    try:
        from app.services.dashboard.comparativo_dashboard import get_monthly_comparison_data
        
        # Parâmetros de filtro
        year = request.args.get("year", type=int) or datetime.now().year
        comparison_mode = request.args.get("comparison_mode", "all")  # 'all', 'single', 'comparison'
        
        # Seleção de meses
        selected_months = []
        if comparison_mode == 'single':
            month = request.args.get("selected_month", type=int)
            if month and 1 <= month <= 12:
                selected_months = [month]
        elif comparison_mode == 'comparison':
            months_str = request.args.get("selected_months", "")
            if months_str:
                try:
                    selected_months = [int(m) for m in months_str.split(',') if 1 <= int(m) <= 12]
                except ValueError:
                    selected_months = []

        filters = {
            "condominio_id": request.args.get("condominio_id", type=int),
            "supervisor_id": request.args.get("supervisor_id", type=int),
            "turno": request.args.get("turno", ""),
            "tipo_ocorrencia_id": request.args.get("tipo_ocorrencia_id", type=int),
            "status": request.args.get("status", ""),
            "data_inicio_str": request.args.get("data_inicio", ""),
            "data_fim_str": request.args.get("data_fim", ""),
        }

        # Remove filtros vazios
        filters = {k: v for k, v in filters.items() if v not in [None, ""]}

        # Busca dados
        data = get_monthly_comparison_data(
            year=year, 
            filters=filters, 
            selected_months=selected_months,
            comparison_mode=comparison_mode
        )
        
        def format_breakdown_list(items):
            return [{"name": item[0], "value": item[1]} for item in items]
            
        formatted_breakdown = {
            "rondas_por_condominio": format_breakdown_list(data["breakdown"]["rondas_por_condominio"]),
            "ocorrencias_por_condominio": format_breakdown_list(data["breakdown"]["ocorrencias_por_condominio"]),
            "paradas_por_condominio": format_breakdown_list(data["breakdown"]["paradas_por_condominio"]),
            "rondas_por_supervisor": format_breakdown_list(data["breakdown"]["rondas_por_supervisor"]),
            "ocorrencias_por_supervisor": format_breakdown_list(data["breakdown"]["ocorrencias_por_supervisor"]),
            "paradas_por_supervisor": format_breakdown_list(data["breakdown"]["paradas_por_supervisor"]),
            "rondas_por_turno": format_breakdown_list(data["breakdown"]["rondas_por_turno"]),
            "ocorrencias_por_tipo": format_breakdown_list(data["breakdown"]["ocorrencias_por_tipo"]),
            "ocorrencias_por_status": format_breakdown_list(data["breakdown"]["ocorrencias_por_status"]),
        }
        
        api_data = {
            "selected_year": data["selected_year"],
            "selected_months": data["selected_months"],
            "comparison_mode": data["comparison_mode"],
            "month_labels": data["month_labels"],
            "month_names": data["month_names"],
            "rondas_data": data["rondas_data"],
            "ocorrencias_data": data["ocorrencias_data"],
            "paradas_data": data["paradas_data"],
            "metrics": data["metrics"],
            "breakdown": formatted_breakdown,
            "filters": data["filters"],
            "filter_options": {
                "condominios": [{"id": c.id, "nome": c.nome} for c in data["filter_options"]["condominios"]],
                "supervisors": [{"id": s.id, "username": s.username} for s in data["filter_options"]["supervisors"]],
                "turnos": data["filter_options"]["turnos"],
                "tipos_ocorrencia": [{"id": t.id, "nome": t.nome} for t in data["filter_options"]["tipos_ocorrencia"]],
                "status_list": data["filter_options"]["status_list"]
            }
        }
        
        return success_response(
            data=api_data,
            message='Dados comparativos obtidos com sucesso'
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter dados comparativos do dashboard: {e}", exc_info=True)
        return error_response('Erro interno ao obter dados comparativos', status_code=500) 