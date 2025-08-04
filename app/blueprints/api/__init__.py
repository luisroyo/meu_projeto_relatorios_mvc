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