"""
APIs de administração para fornecer dados para o frontend.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.condominio import Condominio
from app.models.ocorrencia_tipo import OcorrenciaTipo
from app.models.colaborador import Colaborador
from app.models.orgao_publico import OrgaoPublico
from app import db
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

def admin_required(f):
    """Decorator para verificar se o usuário é admin."""
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== USUÁRIOS ====================

@admin_api_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def listar_usuarios():
    """Listar usuários com paginação."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = User.query.order_by(desc(User.date_registered))
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        usuarios = []
        for user in pagination.items:
            usuarios.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_supervisor': user.is_supervisor,
                'is_approved': user.is_approved,
                'date_registered': user.date_registered.isoformat() if user.date_registered else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        return jsonify({
            'usuarios': usuarios,
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
        logger.error(f"Erro ao listar usuários: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_api_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def obter_usuario(user_id):
    """Obter detalhes de um usuário específico."""
    try:
        user = User.query.get_or_404(user_id)
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_supervisor': user.is_supervisor,
            'is_approved': user.is_approved,
            'date_registered': user.date_registered.isoformat() if user.date_registered else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_api_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def atualizar_usuario(user_id):
    """Atualizar usuário."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Atualizar campos
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        if 'is_supervisor' in data:
            user.is_supervisor = data['is_supervisor']
        if 'is_approved' in data:
            user.is_approved = data['is_approved']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário atualizado com sucesso',
            'user_id': user.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def deletar_usuario(user_id):
    """Deletar usuário."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Não permitir deletar o próprio usuário
        current_user_id = get_jwt_identity()
        if user.id == current_user_id:
            return jsonify({'error': 'Não é possível deletar seu próprio usuário'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário deletado com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar usuário {user_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== CONDOMÍNIOS ====================

@admin_api_bp.route('/condominios', methods=['GET'])
@jwt_required()
@admin_required
def listar_condominios_admin():
    """Listar condomínios com paginação."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Condominio.query.order_by(Condominio.nome)
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        condominios = []
        for condominio in pagination.items:
            condominios.append({
                'id': condominio.id,
                'nome': condominio.nome,
                'endereco': condominio.endereco,
                'data_criacao': condominio.data_criacao.isoformat() if condominio.data_criacao else None
            })
        
        return jsonify({
            'condominios': condominios,
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
        logger.error(f"Erro ao listar condomínios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_api_bp.route('/condominios', methods=['POST'])
@jwt_required()
@admin_required
def criar_condominio():
    """Criar novo condomínio."""
    try:
        data = request.get_json()
        
        if not data.get('nome'):
            return jsonify({'error': 'Nome do condomínio é obrigatório'}), 400
        
        novo_condominio = Condominio(
            nome=data['nome'],
            endereco=data.get('endereco', '')
        )
        
        db.session.add(novo_condominio)
        db.session.commit()
        
        return jsonify({
            'message': 'Condomínio criado com sucesso',
            'condominio_id': novo_condominio.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar condomínio: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_api_bp.route('/condominios/<int:condominio_id>', methods=['PUT'])
@jwt_required()
@admin_required
def atualizar_condominio(condominio_id):
    """Atualizar condomínio."""
    try:
        condominio = Condominio.query.get_or_404(condominio_id)
        data = request.get_json()
        
        if 'nome' in data:
            condominio.nome = data['nome']
        if 'endereco' in data:
            condominio.endereco = data['endereco']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Condomínio atualizado com sucesso',
            'condominio_id': condominio.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar condomínio {condominio_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_api_bp.route('/condominios/<int:condominio_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def deletar_condominio(condominio_id):
    """Deletar condomínio."""
    try:
        condominio = Condominio.query.get_or_404(condominio_id)
        db.session.delete(condominio)
        db.session.commit()
        
        return jsonify({
            'message': 'Condomínio deletado com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar condomínio {condominio_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== TIPOS DE OCORRÊNCIA ====================

@admin_api_bp.route('/tipos-ocorrencia', methods=['GET'])
@jwt_required()
@admin_required
def listar_tipos_ocorrencia_admin():
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

@admin_api_bp.route('/tipos-ocorrencia', methods=['POST'])
@jwt_required()
@admin_required
def criar_tipo_ocorrencia():
    """Criar novo tipo de ocorrência."""
    try:
        data = request.get_json()
        
        if not data.get('nome'):
            return jsonify({'error': 'Nome do tipo é obrigatório'}), 400
        
        novo_tipo = OcorrenciaTipo(
            nome=data['nome'],
            descricao=data.get('descricao', '')
        )
        
        db.session.add(novo_tipo)
        db.session.commit()
        
        return jsonify({
            'message': 'Tipo de ocorrência criado com sucesso',
            'tipo_id': novo_tipo.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar tipo de ocorrência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== COLABORADORES ====================

@admin_api_bp.route('/colaboradores', methods=['GET'])
@jwt_required()
@admin_required
def listar_colaboradores():
    """Listar colaboradores."""
    try:
        colaboradores = Colaborador.query.order_by(Colaborador.nome_completo).all()
        
        return jsonify({
            'colaboradores': [{
                'id': c.id,
                'nome_completo': c.nome_completo,
                'cargo': c.cargo,
                'matricula': c.matricula,
                'data_admissao': c.data_admissao.isoformat() if c.data_admissao else None,
                'status': c.status
            } for c in colaboradores]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar colaboradores: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== ÓRGÃOS PÚBLICOS ====================

@admin_api_bp.route('/orgaos-publicos', methods=['GET'])
@jwt_required()
@admin_required
def listar_orgaos_publicos():
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
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== ESTATÍSTICAS ADMIN ====================

@admin_api_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def obter_estatisticas_admin():
    """Obter estatísticas administrativas."""
    try:
        # Estatísticas gerais
        total_usuarios = User.query.count()
        total_condominios = Condominio.query.count()
        total_tipos_ocorrencia = OcorrenciaTipo.query.count()
        total_colaboradores = Colaborador.query.count()
        
        # Usuários pendentes de aprovação
        usuarios_pendentes = User.query.filter_by(is_approved=False).count()
        
        return jsonify({
            'stats': {
                'total_usuarios': total_usuarios,
                'total_condominios': total_condominios,
                'total_tipos_ocorrencia': total_tipos_ocorrencia,
                'total_colaboradores': total_colaboradores,
                'usuarios_pendentes': usuarios_pendentes
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas admin: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500 