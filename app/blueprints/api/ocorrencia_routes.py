"""
APIs de ocorrências para fornecer dados para o frontend.
"""
import logging
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc

from app import db
from app.models import Ocorrencia, OcorrenciaTipo, Condominio, User
from app.services import ocorrencia_service
from flask import Blueprint

ocorrencia_api_bp = Blueprint('ocorrencia_api', __name__, url_prefix='/api/ocorrencias')

logger = logging.getLogger(__name__)


def get_user_name(user_id):
    """Obtém o nome do usuário pelo ID."""
    if not user_id:
        return 'N/A'
    try:
        user = User.query.get(user_id)
        return user.username if user else 'N/A'
    except Exception:
        return 'N/A'


@ocorrencia_api_bp.route('/', methods=['GET'])
@jwt_required()
def listar_ocorrencias():
    """Listar ocorrências com filtros e paginação."""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtros
        filters = {
            'status': request.args.get('status', ''),
            'condominio_id': request.args.get('condominio_id', type=int),
            'supervisor_id': request.args.get('supervisor_id', type=int),
            'tipo_id': request.args.get('tipo_id', type=int),
            'data_inicio': request.args.get('data_inicio', ''),
            'data_fim': request.args.get('data_fim', ''),
            'texto_relatorio': request.args.get('texto_relatorio', '')
        }
        
        # Query base
        query = Ocorrencia.query.options(
            db.joinedload(Ocorrencia.tipo),
            db.joinedload(Ocorrencia.condominio),
            db.joinedload(Ocorrencia.supervisor)
        )
        
        # Aplicar filtros usando o service centralizado
        query = ocorrencia_service.apply_ocorrencia_filters(query, filters)
        
        # Ordenação
        query = query.order_by(desc(Ocorrencia.data_hora_ocorrencia))
        
        # Paginação
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serializar ocorrências
        ocorrencias = []
        for o in pagination.items:
            try:
                ocorrencias.append({
                    'id': o.id,
                    'tipo': o.tipo.nome if o.tipo else 'N/A',
                    'condominio': o.condominio.nome if o.condominio else 'N/A',
                    'data_hora_ocorrencia': o.data_hora_ocorrencia.isoformat() if o.data_hora_ocorrencia else None,
                    'descricao': o.relatorio_final,
                    'status': o.status,
                    'endereco': o.endereco_especifico,
                    'turno': o.turno,
                    'data_criacao': o.data_criacao.isoformat() if o.data_criacao else None,
                    'registrado_por': get_user_name(o.registrado_por_user_id),
                    'supervisor': get_user_name(o.supervisor_id),
                    'registrado_por_user_id': o.registrado_por_user_id,
                    'supervisor_id': o.supervisor_id
                })
            except Exception as e:
                logger.error(f"Erro ao serializar ocorrência {o.id}: {e}")
                continue
        
        return jsonify({
            'ocorrencias': ocorrencias,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar ocorrências: {e}")
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
def listar_condominios_ocorrencia():
    """Listar condomínios para ocorrências."""
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

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['GET'])
@jwt_required()
def obter_ocorrencia(ocorrencia_id):
    """Obter detalhes de uma ocorrência específica."""
    try:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        
        return jsonify({
            'id': ocorrencia.id,
            'tipo': ocorrencia.tipo.nome if ocorrencia.tipo else 'N/A',
            'condominio': ocorrencia.condominio.nome if ocorrencia.condominio else 'N/A',
            'data_hora_ocorrencia': ocorrencia.data_hora_ocorrencia.isoformat() if ocorrencia.data_hora_ocorrencia else None,
            'descricao': ocorrencia.relatorio_final,
            'status': ocorrencia.status,
            'endereco': ocorrencia.endereco_especifico,
            'turno': ocorrencia.turno,
            'data_criacao': ocorrencia.data_criacao.isoformat() if ocorrencia.data_criacao else None,
                                'registrado_por': get_user_name(ocorrencia.registrado_por_user_id),
                    'supervisor': get_user_name(ocorrencia.supervisor_id),
            'registrado_por_user_id': ocorrencia.registrado_por_user_id,
            'supervisor_id': ocorrencia.supervisor_id,
            'ocorrencia_tipo_id': ocorrencia.ocorrencia_tipo_id,
            'condominio_id': ocorrencia.condominio_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/', methods=['POST'])
@jwt_required()
def criar_ocorrencia():
    """Criar uma nova ocorrência."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['relatorio_final', 'ocorrencia_tipo_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Criar nova ocorrência
        nova_ocorrencia = Ocorrencia()
        nova_ocorrencia.relatorio_final = data['relatorio_final']
        nova_ocorrencia.ocorrencia_tipo_id = data['ocorrencia_tipo_id']
        nova_ocorrencia.condominio_id = data.get('condominio_id')
        nova_ocorrencia.supervisor_id = data.get('supervisor_id')
        nova_ocorrencia.turno = data.get('turno')
        nova_ocorrencia.status = data.get('status', 'Registrada')
        nova_ocorrencia.endereco_especifico = data.get('endereco_especifico')
        nova_ocorrencia.registrado_por_user_id = current_user_id
        
        db.session.add(nova_ocorrencia)
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência criada com sucesso',
            'id': nova_ocorrencia.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar ocorrência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['PUT'])
@jwt_required()
def editar_ocorrencia(ocorrencia_id):
    """Editar uma ocorrência existente."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        data = request.get_json()
        
        # Atualizar campos
        if 'relatorio_final' in data:
            ocorrencia.relatorio_final = data['relatorio_final']
        if 'ocorrencia_tipo_id' in data:
            ocorrencia.ocorrencia_tipo_id = data['ocorrencia_tipo_id']
        if 'condominio_id' in data:
            ocorrencia.condominio_id = data['condominio_id']
        if 'supervisor_id' in data:
            ocorrencia.supervisor_id = data['supervisor_id']
        if 'turno' in data:
            ocorrencia.turno = data['turno']
        if 'status' in data:
            ocorrencia.status = data['status']
        if 'endereco_especifico' in data:
            ocorrencia.endereco_especifico = data['endereco_especifico']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ocorrência atualizada com sucesso',
            'id': ocorrencia.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao editar ocorrência {ocorrencia_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ocorrencia_api_bp.route('/<int:ocorrencia_id>', methods=['DELETE'])
@jwt_required()
def deletar_ocorrencia(ocorrencia_id):
    """Deletar uma ocorrência."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
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

@ocorrencia_api_bp.route('/<int:ocorrencia_id>/approve', methods=['POST'])
@jwt_required()
def approve_ocorrencia(ocorrencia_id):
    """Aprovar uma ocorrência."""
    ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
    
    if ocorrencia.status == 'Aprovada':
        return jsonify({'message': 'Ocorrência já está aprovada'}), 400
    
    ocorrencia.status = 'Aprovada'
    db.session.commit()
    
    logger.info(f"Ocorrência {ocorrencia_id} aprovada")
    return jsonify({'message': 'Ocorrência aprovada com sucesso'}), 200

@ocorrencia_api_bp.route('/<int:ocorrencia_id>/reject', methods=['POST'])
@jwt_required()
def reject_ocorrencia(ocorrencia_id):
    """Rejeitar uma ocorrência."""
    ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
    
    if ocorrencia.status == 'Rejeitada':
        return jsonify({'message': 'Ocorrência já está rejeitada'}), 400
    
    ocorrencia.status = 'Rejeitada'
    db.session.commit()
    
    logger.info(f"Ocorrência {ocorrencia_id} rejeitada")
    return jsonify({'message': 'Ocorrência rejeitada com sucesso'}), 200

@ocorrencia_api_bp.route('/analyze-report', methods=['POST'])
@jwt_required()
def analyze_report():
    """Analisar relatório usando IA."""
    data = request.get_json()
    
    if not data or not data.get('relatorio_bruto'):
        return jsonify({'error': 'Relatório bruto é obrigatório'}), 400
    
    try:
        from app.utils.classificador import classificar_ocorrencia
        from app.services.patrimonial_report_service import PatrimonialReportService
        
        # Classificar ocorrência
        classificacao = classificar_ocorrencia(data['relatorio_bruto'])
        
        # Processar relatório patrimonial
        patrimonial_service = PatrimonialReportService()
        relatorio_processado = patrimonial_service.gerar_relatorio_seguranca(data['relatorio_bruto'])
        
        return jsonify({
            'classificacao': classificacao,
            'relatorio_processado': relatorio_processado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao analisar relatório: {e}")
        return jsonify({'error': 'Erro ao analisar relatório'}), 500 