from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Importar todas as rotas da API
from . import (
    auth_routes,
    dashboard_routes,
    ocorrencia_routes,
    ronda_routes,
    admin_routes,
    ronda_tempo_real_routes,
    ronda_esporadica_consolidacao_routes,
    analisador_routes,
    config_routes
)

# Adicionar rotas específicas para compatibilidade com frontend
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.condominio import Condominio

@api_bp.route('/users', methods=['GET'])
@api_bp.route('/users/', methods=['GET'])
@jwt_required()
def list_users_simple():
    """Listar usuários para filtros do frontend."""
    try:
        users = User.query.filter_by(is_approved=True).order_by(User.username).all()
        return jsonify({
            'users': [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_supervisor': user.is_supervisor,
                'is_admin': user.is_admin,
                'is_approved': user.is_approved
            } for user in users]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erro ao listar usuários'}), 500

@api_bp.route('/condominios', methods=['GET'])
@api_bp.route('/condominios/', methods=['GET'])
@jwt_required()
def list_condominios_simple():
    """Listar condomínios para filtros do frontend."""
    try:
        condominios = Condominio.query.order_by(Condominio.nome).all()
        return jsonify({
            'condominios': [{
                'id': condominio.id,
                'nome': condominio.nome
            } for condominio in condominios]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erro ao listar condomínios'}), 500

# NOTA: ronda_esporadica_routes.py está DEPRECATED
# Use ronda_tempo_real_routes.py em vez disso

# Adicionar rotas de colaboradores e logradouros para compatibilidade com frontend
from app.models.colaborador import Colaborador
from app.models.vw_logradouros import VWLogradouros

@api_bp.route('/colaboradores', methods=['GET'])
@jwt_required()
def list_colaboradores_simple():
    """Listar colaboradores para filtros do frontend."""
    try:
        nome = request.args.get('nome', '')
        query = Colaborador.query.filter_by(status='Ativo')
        
        if nome:
            query = query.filter(Colaborador.nome_completo.ilike(f'%{nome}%'))
        
        colaboradores = query.order_by(Colaborador.nome_completo).limit(10).all()
        
        return jsonify({
            'colaboradores': [{
                'id': col.id,
                'nome_completo': col.nome_completo,
                'cargo': col.cargo,
                'matricula': col.matricula
            } for col in colaboradores]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erro ao listar colaboradores'}), 500

@api_bp.route('/logradouros_view', methods=['GET'])
@jwt_required()
def list_logradouros_simple():
    """Listar logradouros para filtros do frontend."""
    try:
        nome = request.args.get('nome', '')
        query = VWLogradouros.query
        
        if nome:
            query = query.filter(VWLogradouros.nome.ilike(f'%{nome}%'))
        
        logradouros = query.order_by(VWLogradouros.nome).limit(10).all()
        
        return jsonify({
            'logradouros': [{
                'id': log.id,
                'nome': log.nome
            } for log in logradouros]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erro ao listar logradouros'}), 500 

# Adicionar alias para login para compatibilidade com frontend
@api_bp.route('/login', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)  # Opcional para login
def login_alias():
    """Alias para /api/auth/login para compatibilidade com frontend."""
    # Redirecionar para a rota de login do auth blueprint
    from app.blueprints.auth.routes import api_login
    return api_login() 