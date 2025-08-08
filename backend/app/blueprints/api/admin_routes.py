"""
APIs de administração para gerenciamento de usuários, colaboradores, escalas e ferramentas.
"""
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.colaborador import Colaborador
from app.models.escala_mensal import EscalaMensal
from app.services.escala_service import get_escala_mensal, salvar_escala_mensal
from app.services.justificativa_service import JustificativaAtestadoService
from app.services.justificativa_troca_plantao_service import JustificativaTrocaPlantaoService
from app.services.dashboard.comparativo_dashboard import get_monthly_comparison_data
from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data
from app.services.dashboard.ronda_dashboard import get_ronda_dashboard_data
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

def admin_required(f):
    """Decorator para verificar se o usuário é admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# GERENCIAMENTO DE USUÁRIOS
# ============================================================================

@admin_api_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    """Listar todos os usuários com paginação."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    users_pagination = User.query.order_by(User.date_registered.desc()).paginate(
        page=page, per_page=per_page
    )
    
    users = []
    for user in users_pagination.items:
        users.append({
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
        'users': users,
        'pagination': {
            'page': users_pagination.page,
            'pages': users_pagination.pages,
            'per_page': users_pagination.per_page,
            'total': users_pagination.total,
            'has_next': users_pagination.has_next,
            'has_prev': users_pagination.has_prev
        }
    }), 200

@admin_api_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
@admin_required
def approve_user(user_id):
    """Aprovar um usuário."""
    user = User.query.get_or_404(user_id)
    
    if user.is_approved:
        return jsonify({'message': 'Usuário já está aprovado'}), 400
    
    user.is_approved = True
    db.session.commit()
    
    logger.info(f"Usuário {user.username} aprovado")
    return jsonify({'message': f'Usuário {user.username} aprovado com sucesso'}), 200

@admin_api_bp.route('/users/<int:user_id>/revoke', methods=['POST'])
@jwt_required()
@admin_required
def revoke_user(user_id):
    """Revogar aprovação de um usuário."""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user_id:
        return jsonify({'error': 'Você não pode revogar sua própria aprovação'}), 400
    
    if not user.is_approved:
        return jsonify({'message': 'Usuário já não está aprovado'}), 400
    
    user.is_approved = False
    db.session.commit()
    
    logger.info(f"Aprovação de {user.username} foi revogada")
    return jsonify({'message': f'Aprovação de {user.username} foi revogada'}), 200

@admin_api_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@jwt_required()
@admin_required
def toggle_admin(user_id):
    """Alternar status de administrador de um usuário."""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user_id:
        return jsonify({'error': 'Você não pode alterar seu próprio status de administrador'}), 400
    
    user.is_admin = not user.is_admin
    if user.is_admin and not user.is_approved:
        user.is_approved = True
    
    db.session.commit()
    
    status = "promovido a administrador" if user.is_admin else "rebaixado de administrador"
    logger.info(f"Usuário {user.username} foi {status}")
    
    return jsonify({
        'message': f'Usuário {user.username} foi {status} com sucesso',
        'is_admin': user.is_admin
    }), 200

@admin_api_bp.route('/users/<int:user_id>/toggle-supervisor', methods=['POST'])
@jwt_required()
@admin_required
def toggle_supervisor(user_id):
    """Alternar status de supervisor de um usuário."""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user_id:
        return jsonify({'error': 'Você não pode alterar seu próprio status de supervisor'}), 400
    
    user.is_supervisor = not user.is_supervisor
    if user.is_supervisor and not user.is_approved:
        user.is_approved = True
    
    db.session.commit()
    
    status = "promovido a supervisor" if user.is_supervisor else "rebaixado de supervisor"
    logger.info(f"Usuário {user.username} foi {status}")
    
    return jsonify({
        'message': f'Usuário {user.username} foi {status} com sucesso',
        'is_supervisor': user.is_supervisor
    }), 200

@admin_api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Deletar um usuário."""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user_id:
        return jsonify({'error': 'Você não pode deletar sua própria conta'}), 400
    
    try:
        from app.services.user_service import delete_user_and_dependencies
        delete_user_and_dependencies(user)
        db.session.commit()
        
        logger.info(f"Usuário {user.username} foi deletado")
        return jsonify({'message': f'Usuário {user.username} foi deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar usuário {user.username}: {e}")
        return jsonify({'error': 'Erro ao deletar usuário'}), 500

# ============================================================================
# GERENCIAMENTO DE COLABORADORES
# ============================================================================

@admin_api_bp.route('/colaboradores', methods=['GET'])
@admin_api_bp.route('/colaboradores/search', methods=['GET'])
@jwt_required()
@admin_required
def list_colaboradores():
    """Listar colaboradores com paginação e busca."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 'Ativo')
    nome = request.args.get('nome', '')
    
    query = Colaborador.query
    if status:
        query = query.filter_by(status=status)
    if nome:
        query = query.filter(Colaborador.nome_completo.ilike(f'%{nome}%'))
    
    colaboradores_pagination = query.order_by(Colaborador.nome_completo).paginate(
        page=page, per_page=per_page
    )
    
    colaboradores = []
    for col in colaboradores_pagination.items:
        colaboradores.append({
            'id': col.id,
            'nome_completo': col.nome_completo,
            'cargo': col.cargo,
            'matricula': col.matricula,
            'data_admissao': col.data_admissao.isoformat() if col.data_admissao else None,
            'status': col.status
        })
    
    return jsonify({
        'colaboradores': colaboradores,
        'pagination': {
            'page': colaboradores_pagination.page,
            'pages': colaboradores_pagination.pages,
            'per_page': colaboradores_pagination.per_page,
            'total': colaboradores_pagination.total,
            'has_next': colaboradores_pagination.has_next,
            'has_prev': colaboradores_pagination.has_prev
        }
    }), 200

@admin_api_bp.route('/colaboradores', methods=['POST'])
@jwt_required()
@admin_required
def create_colaborador():
    """Criar novo colaborador."""
    data = request.get_json()
    
    required_fields = ['nome_completo', 'cargo', 'data_admissao', 'status']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400
    
    try:
        novo_colaborador = Colaborador(
            nome_completo=data['nome_completo'],
            cargo=data['cargo'],
            matricula=data.get('matricula'),
            data_admissao=datetime.fromisoformat(data['data_admissao']),
            status=data['status']
        )
        
        db.session.add(novo_colaborador)
        db.session.commit()
        
        logger.info(f"Colaborador {novo_colaborador.nome_completo} criado")
        
        return jsonify({
            'message': f'Colaborador {novo_colaborador.nome_completo} criado com sucesso',
            'colaborador': {
                'id': novo_colaborador.id,
                'nome_completo': novo_colaborador.nome_completo,
                'cargo': novo_colaborador.cargo,
                'matricula': novo_colaborador.matricula,
                'data_admissao': novo_colaborador.data_admissao.isoformat() if novo_colaborador.data_admissao else None,
                'status': novo_colaborador.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar colaborador: {e}")
        return jsonify({'error': 'Erro ao criar colaborador'}), 500

@admin_api_bp.route('/colaboradores/<int:colaborador_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_colaborador(colaborador_id):
    """Obter detalhes de um colaborador."""
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    
    return jsonify({
        'id': colaborador.id,
        'nome_completo': colaborador.nome_completo,
        'cargo': colaborador.cargo,
        'matricula': colaborador.matricula,
        'data_admissao': colaborador.data_admissao.isoformat() if colaborador.data_admissao else None,
        'status': colaborador.status
    }), 200

@admin_api_bp.route('/colaboradores/<int:colaborador_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_colaborador(colaborador_id):
    """Atualizar colaborador."""
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    data = request.get_json()
    
    try:
        if 'nome_completo' in data:
            colaborador.nome_completo = data['nome_completo']
        if 'cargo' in data:
            colaborador.cargo = data['cargo']
        if 'matricula' in data:
            colaborador.matricula = data['matricula']
        if 'data_admissao' in data:
            colaborador.data_admissao = datetime.fromisoformat(data['data_admissao'])
        if 'status' in data:
            colaborador.status = data['status']
        
        db.session.commit()
        
        logger.info(f"Colaborador {colaborador.nome_completo} atualizado")
        
        return jsonify({
            'message': f'Colaborador {colaborador.nome_completo} atualizado com sucesso',
            'colaborador': {
                'id': colaborador.id,
                'nome_completo': colaborador.nome_completo,
                'cargo': colaborador.cargo,
                'matricula': colaborador.matricula,
                'data_admissao': colaborador.data_admissao.isoformat() if colaborador.data_admissao else None,
                'status': colaborador.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar colaborador: {e}")
        return jsonify({'error': 'Erro ao atualizar colaborador'}), 500

@admin_api_bp.route('/colaboradores/<int:colaborador_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_colaborador(colaborador_id):
    """Deletar colaborador (soft delete)."""
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    
    try:
        colaborador.status = 'Inativo'
        db.session.commit()
        
        logger.info(f"Colaborador {colaborador.nome_completo} marcado como inativo")
        return jsonify({'message': f'Colaborador {colaborador.nome_completo} deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar colaborador: {e}")
        return jsonify({'error': 'Erro ao deletar colaborador'}), 500

# ============================================================================
# GERENCIAMENTO DE ESCALAS
# ============================================================================

@admin_api_bp.route('/escalas', methods=['GET'])
@jwt_required()
@admin_required
def get_escalas():
    """Obter escalas mensais."""
    ano = request.args.get('ano', datetime.now().year, type=int)
    mes = request.args.get('mes', datetime.now().month, type=int)
    
    try:
        escalas = get_escala_mensal(ano, mes)
        supervisores = User.query.filter_by(is_supervisor=True, is_approved=True).order_by(User.username).all()
        
        return jsonify({
            'escalas': escalas,
            'supervisores': [{'id': s.id, 'username': s.username} for s in supervisores],
            'ano': ano,
            'mes': mes
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter escalas: {e}")
        return jsonify({'error': 'Erro ao obter escalas'}), 500

@admin_api_bp.route('/escalas', methods=['POST'])
@jwt_required()
@admin_required
def save_escalas():
    """Salvar escalas mensais."""
    data = request.get_json()
    
    if not data.get('ano') or not data.get('mes') or not data.get('escalas'):
        return jsonify({'error': 'Ano, mês e escalas são obrigatórios'}), 400
    
    try:
        sucesso, mensagem = salvar_escala_mensal(data['ano'], data['mes'], data['escalas'])
        
        if sucesso:
            return jsonify({'message': mensagem}), 200
        else:
            return jsonify({'error': mensagem}), 400
            
    except Exception as e:
        logger.error(f"Erro ao salvar escalas: {e}")
        return jsonify({'error': 'Erro ao salvar escalas'}), 500

# ============================================================================
# FERRAMENTAS ADMINISTRATIVAS
# ============================================================================

@admin_api_bp.route('/tools/justificativa-atestado', methods=['POST'])
@jwt_required()
@admin_required
def generate_justificativa_atestado():
    """Gerar justificativa de atestado médico."""
    data = request.get_json()
    
    if not data.get('texto_atestado'):
        return jsonify({'error': 'Texto do atestado é obrigatório'}), 400
    
    try:
        service = JustificativaAtestadoService()
        justificativa = service.gerar_justificativa(data['texto_atestado'])
        
        return jsonify({
            'justificativa': justificativa
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar justificativa de atestado: {e}")
        return jsonify({'error': 'Erro ao gerar justificativa'}), 500

@admin_api_bp.route('/tools/justificativa-troca-plantao', methods=['POST'])
@jwt_required()
@admin_required
def generate_justificativa_troca_plantao():
    """Gerar justificativa de troca de plantão."""
    data = request.get_json()
    
    if not data.get('dados_troca'):
        return jsonify({'error': 'Dados da troca são obrigatórios'}), 400
    
    try:
        service = JustificativaTrocaPlantaoService()
        justificativa = service.gerar_justificativa(data['dados_troca'])
        
        return jsonify({
            'justificativa': justificativa
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar justificativa de troca de plantão: {e}")
        return jsonify({'error': 'Erro ao gerar justificativa'}), 500

@admin_api_bp.route('/tools/formatar-email', methods=['POST'])
@jwt_required()
@admin_required
def formatar_email():
    """Formatar email profissional."""
    data = request.get_json()
    
    if not data.get('conteudo'):
        return jsonify({'error': 'Conteúdo é obrigatório'}), 400
    
    try:
        from app.services.email_format_service import EmailFormatService
        service = EmailFormatService()
        email_formatado = service.formatar_email(data['conteudo'])
        
        return jsonify({
            'email_formatado': email_formatado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao formatar email: {e}")
        return jsonify({'error': 'Erro ao formatar email'}), 500

# ============================================================================
# DASHBOARDS ESPECÍFICOS
# ============================================================================

@admin_api_bp.route('/dashboard/comparativo', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard_comparativo():
    """Obter dados do dashboard comparativo."""
    ano = request.args.get('ano', datetime.now().year, type=int)
    mes = request.args.get('mes', datetime.now().month, type=int)
    
    try:
        dados = get_monthly_comparison_data(ano, mes)
        return jsonify(dados), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter dashboard comparativo: {e}")
        return jsonify({'error': 'Erro ao obter dados comparativos'}), 500

@admin_api_bp.route('/dashboard/ocorrencias', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard_ocorrencias():
    """Obter dados do dashboard de ocorrências."""
    ano = request.args.get('ano', datetime.now().year, type=int)
    mes = request.args.get('mes', datetime.now().month, type=int)
    
    try:
        dados = get_ocorrencia_dashboard_data(ano, mes)
        return jsonify(dados), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter dashboard de ocorrências: {e}")
        return jsonify({'error': 'Erro ao obter dados de ocorrências'}), 500

@admin_api_bp.route('/dashboard/rondas', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard_rondas():
    """Obter dados do dashboard de rondas."""
    ano = request.args.get('ano', datetime.now().year, type=int)
    mes = request.args.get('mes', datetime.now().month, type=int)
    
    try:
        dados = get_ronda_dashboard_data(ano, mes)
        return jsonify(dados), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter dashboard de rondas: {e}")
        return jsonify({'error': 'Erro ao obter dados de rondas'}), 500 