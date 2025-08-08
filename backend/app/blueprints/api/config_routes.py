"""
APIs para gerenciar configurações do sistema.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.ocorrencia_tipo import OcorrenciaTipo
from app.models.orgao_publico import OrgaoPublico
from app.models.logradouro import Logradouro
from app.models.condominio import Condominio
from app import db
import logging

logger = logging.getLogger(__name__)

config_api_bp = Blueprint('config_api', __name__, url_prefix='/api/config')

def admin_required(f):
    """Decorator para verificar se o usuário é admin."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# TIPOS DE OCORRÊNCIA
# ============================================================================

@config_api_bp.route('/tipos-ocorrencia', methods=['GET'])
@jwt_required()
def list_tipos_ocorrencia():
    """Listar tipos de ocorrência."""
    try:
        tipos = OcorrenciaTipo.query.order_by(OcorrenciaTipo.nome).all()
        
        return jsonify({
            'tipos': [{
                'id': t.id,
                'nome': t.nome,
                'descricao': t.descricao
            } for t in tipos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar tipos de ocorrência: {e}")
        return jsonify({'error': 'Erro ao listar tipos de ocorrência'}), 500

@config_api_bp.route('/tipos-ocorrencia', methods=['POST'])
@jwt_required()
@admin_required
def create_tipo_ocorrencia():
    """Criar novo tipo de ocorrência."""
    data = request.get_json()
    
    if not data or not data.get('nome'):
        return jsonify({'error': 'Nome do tipo é obrigatório'}), 400
    
    try:
        novo_tipo = OcorrenciaTipo(
            nome=data['nome'],
            descricao=data.get('descricao', '')
        )
        
        db.session.add(novo_tipo)
        db.session.commit()
        
        logger.info(f"Tipo de ocorrência {novo_tipo.nome} criado")
        
        return jsonify({
            'message': f'Tipo de ocorrência {novo_tipo.nome} criado com sucesso',
            'tipo': {
                'id': novo_tipo.id,
                'nome': novo_tipo.nome,
                'descricao': novo_tipo.descricao
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar tipo de ocorrência: {e}")
        return jsonify({'error': 'Erro ao criar tipo de ocorrência'}), 500

@config_api_bp.route('/tipos-ocorrencia/<int:tipo_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_tipo_ocorrencia(tipo_id):
    """Atualizar tipo de ocorrência."""
    tipo = OcorrenciaTipo.query.get_or_404(tipo_id)
    data = request.get_json()
    
    try:
        if 'nome' in data:
            tipo.nome = data['nome']
        if 'descricao' in data:
            tipo.descricao = data['descricao']
        
        db.session.commit()
        
        logger.info(f"Tipo de ocorrência {tipo.nome} atualizado")
        
        return jsonify({
            'message': f'Tipo de ocorrência {tipo.nome} atualizado com sucesso',
            'tipo': {
                'id': tipo.id,
                'nome': tipo.nome,
                'descricao': tipo.descricao
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar tipo de ocorrência: {e}")
        return jsonify({'error': 'Erro ao atualizar tipo de ocorrência'}), 500

@config_api_bp.route('/tipos-ocorrencia/<int:tipo_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_tipo_ocorrencia(tipo_id):
    """Deletar tipo de ocorrência."""
    tipo = OcorrenciaTipo.query.get_or_404(tipo_id)
    
    try:
        db.session.delete(tipo)
        db.session.commit()
        
        logger.info(f"Tipo de ocorrência {tipo.nome} deletado")
        return jsonify({'message': f'Tipo de ocorrência {tipo.nome} deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar tipo de ocorrência: {e}")
        return jsonify({'error': 'Erro ao deletar tipo de ocorrência'}), 500

# ============================================================================
# ÓRGÃOS PÚBLICOS
# ============================================================================

@config_api_bp.route('/orgaos-publicos', methods=['GET'])
@jwt_required()
def list_orgaos_publicos():
    """Listar órgãos públicos."""
    try:
        orgaos = OrgaoPublico.query.order_by(OrgaoPublico.nome).all()
        
        return jsonify({
            'orgaos': [{
                'id': o.id,
                'nome': o.nome,
                'tipo': o.tipo,
                'contato': o.contato
            } for o in orgaos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar órgãos públicos: {e}")
        return jsonify({'error': 'Erro ao listar órgãos públicos'}), 500

@config_api_bp.route('/orgaos-publicos', methods=['POST'])
@jwt_required()
@admin_required
def create_orgao_publico():
    """Criar novo órgão público."""
    data = request.get_json()
    
    if not data or not data.get('nome'):
        return jsonify({'error': 'Nome do órgão é obrigatório'}), 400
    
    try:
        novo_orgao = OrgaoPublico(
            nome=data['nome'],
            tipo=data.get('tipo', ''),
            contato=data.get('contato', '')
        )
        
        db.session.add(novo_orgao)
        db.session.commit()
        
        logger.info(f"Órgão público {novo_orgao.nome} criado")
        
        return jsonify({
            'message': f'Órgão público {novo_orgao.nome} criado com sucesso',
            'orgao': {
                'id': novo_orgao.id,
                'nome': novo_orgao.nome,
                'tipo': novo_orgao.tipo,
                'contato': novo_orgao.contato
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar órgão público: {e}")
        return jsonify({'error': 'Erro ao criar órgão público'}), 500

@config_api_bp.route('/orgaos-publicos/<int:orgao_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_orgao_publico(orgao_id):
    """Atualizar órgão público."""
    orgao = OrgaoPublico.query.get_or_404(orgao_id)
    data = request.get_json()
    
    try:
        if 'nome' in data:
            orgao.nome = data['nome']
        if 'tipo' in data:
            orgao.tipo = data['tipo']
        if 'contato' in data:
            orgao.contato = data['contato']
        
        db.session.commit()
        
        logger.info(f"Órgão público {orgao.nome} atualizado")
        
        return jsonify({
            'message': f'Órgão público {orgao.nome} atualizado com sucesso',
            'orgao': {
                'id': orgao.id,
                'nome': orgao.nome,
                'tipo': orgao.tipo,
                'contato': orgao.contato
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar órgão público: {e}")
        return jsonify({'error': 'Erro ao atualizar órgão público'}), 500

@config_api_bp.route('/orgaos-publicos/<int:orgao_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_orgao_publico(orgao_id):
    """Deletar órgão público."""
    orgao = OrgaoPublico.query.get_or_404(orgao_id)
    
    try:
        db.session.delete(orgao)
        db.session.commit()
        
        logger.info(f"Órgão público {orgao.nome} deletado")
        return jsonify({'message': f'Órgão público {orgao.nome} deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar órgão público: {e}")
        return jsonify({'error': 'Erro ao deletar órgão público'}), 500

# ============================================================================
# LOGRADOUROS
# ============================================================================

@config_api_bp.route('/logradouros', methods=['GET'])
@jwt_required()
def list_logradouros():
    """Listar logradouros."""
    try:
        logradouros = Logradouro.query.order_by(Logradouro.nome).all()
        
        return jsonify({
            'logradouros': [{
                'id': l.id,
                'nome': l.nome
            } for l in logradouros]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar logradouros: {e}")
        return jsonify({'error': 'Erro ao listar logradouros'}), 500

@config_api_bp.route('/logradouros', methods=['POST'])
@jwt_required()
@admin_required
def create_logradouro():
    """Criar novo logradouro."""
    data = request.get_json()
    
    if not data or not data.get('nome'):
        return jsonify({'error': 'Nome do logradouro é obrigatório'}), 400
    
    try:
        novo_logradouro = Logradouro(nome=data['nome'])
        
        db.session.add(novo_logradouro)
        db.session.commit()
        
        logger.info(f"Logradouro {novo_logradouro.nome} criado")
        
        return jsonify({
            'message': f'Logradouro {novo_logradouro.nome} criado com sucesso',
            'logradouro': {
                'id': novo_logradouro.id,
                'nome': novo_logradouro.nome
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar logradouro: {e}")
        return jsonify({'error': 'Erro ao criar logradouro'}), 500

# ============================================================================
# CONDOMÍNIOS
# ============================================================================

@config_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
def list_condominios():
    """Listar condomínios."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        
        return jsonify({
            'condominios': [{
                'id': c.id,
                'nome': c.nome
            } for c in condominios]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        return jsonify({'error': 'Erro ao listar condomínios'}), 500

@config_api_bp.route('/condominios', methods=['POST'])
@jwt_required()
@admin_required
def create_condominio():
    """Criar novo condomínio."""
    data = request.get_json()
    
    if not data or not data.get('nome'):
        return jsonify({'error': 'Nome do condomínio é obrigatório'}), 400
    
    try:
        novo_condominio = Condominio(
            nome=data['nome']
        )
        
        db.session.add(novo_condominio)
        db.session.commit()
        
        logger.info(f"Condomínio {novo_condominio.nome} criado")
        
        return jsonify({
            'message': f'Condomínio {novo_condominio.nome} criado com sucesso',
            'condominio': {
                'id': novo_condominio.id,
                'nome': novo_condominio.nome
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar condomínio: {e}")
        return jsonify({'error': 'Erro ao criar condomínio'}), 500

@config_api_bp.route('/condominios/<int:condominio_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_condominio(condominio_id):
    """Atualizar condomínio."""
    condominio = Condominio.query.get_or_404(condominio_id)
    data = request.get_json()
    
    try:
        if 'nome' in data:
            condominio.nome = data['nome']
        
        db.session.commit()
        
        logger.info(f"Condomínio {condominio.nome} atualizado")
        
        return jsonify({
            'message': f'Condomínio {condominio.nome} atualizado com sucesso',
            'condominio': {
                'id': condominio.id,
                'nome': condominio.nome
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar condomínio: {e}")
        return jsonify({'error': 'Erro ao atualizar condomínio'}), 500

@config_api_bp.route('/condominios/<int:condominio_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_condominio(condominio_id):
    """Deletar condomínio."""
    condominio = Condominio.query.get_or_404(condominio_id)
    
    try:
        db.session.delete(condominio)
        db.session.commit()
        
        logger.info(f"Condomínio {condominio.nome} deletado")
        return jsonify({'message': f'Condomínio {condominio.nome} deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar condomínio: {e}")
        return jsonify({'error': 'Erro ao deletar condomínio'}), 500 