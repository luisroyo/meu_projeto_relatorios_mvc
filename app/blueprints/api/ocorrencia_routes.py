"""
APIs de ocorrências para fornecer dados para o frontend.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.ocorrencia import Ocorrencia
from app.models.condominio import Condominio
from app.models.ocorrencia_tipo import OcorrenciaTipo
from app import db
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

ocorrencia_api_bp = Blueprint('ocorrencia_api', __name__, url_prefix='/api/ocorrencias')

@ocorrencia_api_bp.route('/', methods=['GET'])
@jwt_required()
def listar_ocorrencias():
    """Listar ocorrências com paginação e filtros."""
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
        tipo_id = request.args.get('tipo_id', type=int)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query base
        query = Ocorrencia.query
        
        # Aplicar filtros
        if condominio_id:
            query = query.filter(Ocorrencia.condominio_id == condominio_id)
        if tipo_id:
            query = query.filter(Ocorrencia.tipo_ocorrencia_id == tipo_id)
        if data_inicio:
            query = query.filter(Ocorrencia.data_ocorrencia >= data_inicio)
        if data_fim:
            query = query.filter(Ocorrencia.data_ocorrencia <= data_fim)
        
        # Ordenar por data mais recente
        query = query.order_by(desc(Ocorrencia.data_ocorrencia))
        
        # Paginação
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        ocorrencias = []
        for ocorrencia in pagination.items:
            ocorrencias.append({
                'id': ocorrencia.id,
                'tipo': ocorrencia.tipo_ocorrencia.nome if ocorrencia.tipo_ocorrencia else 'N/A',
                'condominio': ocorrencia.condominio.nome if ocorrencia.condominio else 'N/A',
                'data_ocorrencia': ocorrencia.data_ocorrencia.isoformat() if ocorrencia.data_ocorrencia else None,
                'hora_ocorrencia': ocorrencia.hora_ocorrencia.isoformat() if ocorrencia.hora_ocorrencia else None,
                'descricao': ocorrencia.descricao,
                'local': ocorrencia.local,
                'envolvidos': ocorrencia.envolvidos,
                'acoes_tomadas': ocorrencia.acoes_tomadas,
                'status': ocorrencia.status,
                'registrado_por': ocorrencia.registrado_por.username if ocorrencia.registrado_por else 'N/A',
                'data_registro': ocorrencia.data_registro.isoformat() if ocorrencia.data_registro else None
            })
        
        return jsonify({
            'ocorrencias': ocorrencias,
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
        logger.error(f"Erro ao listar ocorrências: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['GET'])
@jwt_required()
def obter_ocorrencia(ocorrencia_id):
    """Obter detalhes de uma ocorrência específica."""
    try:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        
        return jsonify({
            'id': ocorrencia.id,
            'tipo': {
                'id': ocorrencia.tipo_ocorrencia.id,
                'nome': ocorrencia.tipo_ocorrencia.nome
            } if ocorrencia.tipo_ocorrencia else None,
            'condominio': {
                'id': ocorrencia.condominio.id,
                'nome': ocorrencia.condominio.nome
            } if ocorrencia.condominio else None,
            'data_ocorrencia': ocorrencia.data_ocorrencia.isoformat() if ocorrencia.data_ocorrencia else None,
            'hora_ocorrencia': ocorrencia.hora_ocorrencia.isoformat() if ocorrencia.hora_ocorrencia else None,
            'descricao': ocorrencia.descricao,
            'local': ocorrencia.local,
            'envolvidos': ocorrencia.envolvidos,
            'acoes_tomadas': ocorrencia.acoes_tomadas,
            'status': ocorrencia.status,
            'registrado_por': {
                'id': ocorrencia.registrado_por.id,
                'username': ocorrencia.registrado_por.username
            } if ocorrencia.registrado_por else None,
            'data_registro': ocorrencia.data_registro.isoformat() if ocorrencia.data_registro else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/', methods=['POST'])
@jwt_required()
def criar_ocorrencia():
    """Criar nova ocorrência."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        data = request.get_json()
        
        # Validações básicas
        if not data.get('tipo_ocorrencia_id'):
            return jsonify({'error': 'Tipo de ocorrência é obrigatório'}), 400
        if not data.get('condominio_id'):
            return jsonify({'error': 'Condomínio é obrigatório'}), 400
        if not data.get('descricao'):
            return jsonify({'error': 'Descrição é obrigatória'}), 400
        
        # Criar nova ocorrência
        nova_ocorrencia = Ocorrencia(
            tipo_ocorrencia_id=data['tipo_ocorrencia_id'],
            condominio_id=data['condominio_id'],
            data_ocorrencia=data.get('data_ocorrencia'),
            hora_ocorrencia=data.get('hora_ocorrencia'),
            descricao=data['descricao'],
            local=data.get('local'),
            envolvidos=data.get('envolvidos'),
            acoes_tomadas=data.get('acoes_tomadas'),
            status=data.get('status', 'pendente'),
            registrado_por_id=user.id
        )
        
        db.session.add(nova_ocorrencia)
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência criada com sucesso',
            'ocorrencia_id': nova_ocorrencia.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ocorrência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['PUT'])
@jwt_required()
def atualizar_ocorrencia(ocorrencia_id):
    """Atualizar ocorrência existente."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        data = request.get_json()
        
        # Atualizar campos
        if 'tipo_ocorrencia_id' in data:
            ocorrencia.tipo_ocorrencia_id = data['tipo_ocorrencia_id']
        if 'condominio_id' in data:
            ocorrencia.condominio_id = data['condominio_id']
        if 'data_ocorrencia' in data:
            ocorrencia.data_ocorrencia = data['data_ocorrencia']
        if 'hora_ocorrencia' in data:
            ocorrencia.hora_ocorrencia = data['hora_ocorrencia']
        if 'descricao' in data:
            ocorrencia.descricao = data['descricao']
        if 'local' in data:
            ocorrencia.local = data['local']
        if 'envolvidos' in data:
            ocorrencia.envolvidos = data['envolvidos']
        if 'acoes_tomadas' in data:
            ocorrencia.acoes_tomadas = data['acoes_tomadas']
        if 'status' in data:
            ocorrencia.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência atualizada com sucesso',
            'ocorrencia_id': ocorrencia.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['DELETE'])
@jwt_required()
def deletar_ocorrencia(ocorrencia_id):
    """Deletar ocorrência."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Verificar se é admin
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        db.session.delete(ocorrencia)
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência deletada com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/tipos', methods=['GET'])
@jwt_required()
def listar_tipos_ocorrencia():
    """Listar tipos de ocorrência."""
    try:
        tipos = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
        
        return jsonify({
            'tipos': [{
                'id': tipo.id,
                'nome': tipo.nome,
                'descricao': tipo.descricao
            } for tipo in tipos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar tipos de ocorrência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def listar_condominios():
    """Listar condomínios para filtros."""
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