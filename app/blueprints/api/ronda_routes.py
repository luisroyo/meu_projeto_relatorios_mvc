"""
APIs de rondas para fornecer dados para o frontend.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.ronda_esporadica import RondaEsporadica
from app.models.ronda import Ronda
from app.models.condominio import Condominio
from app.services.ronda_tempo_real_service import RondaTempoRealService
from app.services.ronda_esporadica_consolidacao_service import RondaEsporadicaConsolidacaoService
from app import db
from sqlalchemy import desc
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

ronda_api_bp = Blueprint('ronda_api', __name__, url_prefix='/api/rondas')

@ronda_api_bp.route('/', methods=['GET'])
@jwt_required()
def listar_rondas():
    """Listar rondas com paginação e filtros."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtros
        condominio_id = request.args.get('condominio_id', type=int)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        
        # Query base - rondas esporádicas (tempo real)
        query = RondaEsporadica.query
        
        # Aplicar filtros
        if condominio_id:
            query = query.filter(RondaEsporadica.condominio_id == condominio_id)
        if data_inicio:
            query = query.filter(RondaEsporadica.data_plantao >= data_inicio)
        if data_fim:
            query = query.filter(RondaEsporadica.data_plantao <= data_fim)
        if status:
            query = query.filter(RondaEsporadica.status == status)
        
        # Ordenar por data mais recente
        query = query.order_by(desc(RondaEsporadica.data_plantao))
        
        # Paginação
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        rondas = []
        for ronda in pagination.items:
            rondas.append({
                'id': ronda.id,
                'condominio': ronda.condominio.nome if ronda.condominio else 'N/A',
                'data_plantao': ronda.data_plantao.isoformat() if ronda.data_plantao else None,
                'escala_plantao': ronda.escala_plantao,
                'status': ronda.status,
                'total_rondas': ronda.total_rondas,
                'tempo_total_minutos': ronda.tempo_total_minutos,
                'observacoes': ronda.observacoes,
                'registrado_por': ronda.registrado_por.username if ronda.registrado_por else 'N/A',
                'data_registro': ronda.data_registro.isoformat() if ronda.data_registro else None
            })
        
        return jsonify({
            'rondas': rondas,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar rondas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/<int:ronda_id>', methods=['GET'])
@jwt_required()
def obter_ronda(ronda_id):
    """Obter detalhes de uma ronda específica."""
    try:
        ronda = RondaEsporadica.query.get_or_404(ronda_id)
        
        return jsonify({
            'id': ronda.id,
            'condominio': {
                'id': ronda.condominio.id,
                'nome': ronda.condominio.nome
            } if ronda.condominio else None,
            'data_plantao': ronda.data_plantao.isoformat() if ronda.data_plantao else None,
            'escala_plantao': ronda.escala_plantao,
            'status': ronda.status,
            'total_rondas': ronda.total_rondas,
            'tempo_total_minutos': ronda.tempo_total_minutos,
            'observacoes': ronda.observacoes,
            'registrado_por': {
                'id': ronda.registrado_por.id,
                'username': ronda.registrado_por.username
            } if ronda.registrado_por else None,
            'data_registro': ronda.data_registro.isoformat() if ronda.data_registro else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ronda {ronda_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/em-andamento', methods=['GET'])
@jwt_required()
def listar_rondas_em_andamento():
    """Listar rondas em andamento (tempo real)."""
    try:
        service = RondaTempoRealService()
        rondas = service.listar_rondas_em_andamento()
        
        return jsonify({
            'rondas': rondas
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar rondas em andamento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/iniciar', methods=['POST'])
@jwt_required()
def iniciar_ronda_tempo_real():
    """Iniciar nova ronda em tempo real."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        data = request.get_json()
        
        # Validações básicas
        if not data.get('condominio_id'):
            return jsonify({'error': 'Condomínio é obrigatório'}), 400
        
        service = RondaTempoRealService()
        resultado = service.iniciar_ronda(
            condominio_id=data['condominio_id'],
            hora_entrada=data.get('hora_entrada'),
            observacoes=data.get('observacoes', ''),
            user_id=user.id
        )
        
        if resultado.get('success'):
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        logger.error(f"Erro ao iniciar ronda: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/finalizar/<int:ronda_id>', methods=['POST'])
@jwt_required()
def finalizar_ronda_tempo_real(ronda_id):
    """Finalizar ronda em tempo real."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        data = request.get_json()
        
        service = RondaTempoRealService()
        resultado = service.finalizar_ronda(
            ronda_id=ronda_id,
            hora_saida=data.get('hora_saida'),
            observacoes=data.get('observacoes', ''),
            user_id=user.id
        )
        
        if resultado.get('success'):
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        logger.error(f"Erro ao finalizar ronda: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/cancelar/<int:ronda_id>', methods=['POST'])
@jwt_required()
def cancelar_ronda_tempo_real(ronda_id):
    """Cancelar ronda em tempo real."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        service = RondaTempoRealService()
        resultado = service.cancelar_ronda(
            ronda_id=ronda_id,
            user_id=user.id
        )
        
        if resultado.get('success'):
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
        
    except Exception as e:
        logger.error(f"Erro ao cancelar ronda: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas_tempo_real():
    """Obter estatísticas das rondas em tempo real."""
    try:
        service = RondaTempoRealService()
        estatisticas = service.obter_estatisticas_plantao()
        
        return jsonify(estatisticas), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/tempo-real/hora-atual', methods=['GET'])
@jwt_required()
def obter_hora_atual():
    """Obter hora atual do servidor."""
    try:
        hora_atual = datetime.now().strftime('%H:%M:%S')
        return jsonify({
            'hora_atual': hora_atual
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter hora atual: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/relatorios/gerar', methods=['POST'])
@jwt_required()
def gerar_relatorio_rondas():
    """Gerar relatório de rondas."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        data = request.get_json()
        condominio_id = data.get('condominio_id')  # Opcional, se não fornecido gera para todos
        
        service = RondaEsporadicaConsolidacaoService()
        
        if condominio_id:
            # Relatório para condomínio específico
            relatorio = service.gerar_relatorio_condominio(
                condominio_id=condominio_id,
                data_plantao=date.today()
            )
        else:
            # Relatório para todos os condomínios
            relatorio = service.gerar_relatorio_geral(data_plantao=date.today())
        
        return jsonify({
            'relatorio': relatorio,
            'condominio_id': condominio_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ronda_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def listar_condominios_rondas():
    """Listar condomínios para rondas."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        return jsonify({
            'condominios': [{
                'id': condominio.id,
                'nome': condominio.nome
            } for condominio in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500 