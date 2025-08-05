"""
APIs de autenticação usando JWT.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app import db
import logging

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

@auth_api_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de login que retorna JWT token."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        if not user.is_approved:
            return jsonify({'error': 'Usuário não aprovado'}), 403
        
        access_token = create_access_token(identity=user.id)
        
        logger.info(f"Login bem-sucedido para usuário: {user.email}")
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_supervisor': user.is_supervisor,
                'is_approved': user.is_approved
            }
        }), 200
    
    logger.warning(f"Tentativa de login falhou para email: {data.get('email')}")
    return jsonify({'error': 'Credenciais inválidas'}), 401

@auth_api_bp.route('/register', methods=['POST'])
def register():
    """Endpoint de registro de usuário."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({'error': 'Email, senha e username são obrigatórios'}), 400
    
    # Verificar se usuário já existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 409
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username já cadastrado'}), 409
    
    # Criar novo usuário
    new_user = User(
        username=data['username'],
        email=data['email'],
        is_approved=False,  # Precisa de aprovação do admin
        is_admin=False,
        is_supervisor=False
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"Novo usuário registrado: {new_user.email}")
        
        return jsonify({
            'message': 'Usuário registrado com sucesso. Aguarde aprovação do administrador.',
            'user_id': new_user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao registrar usuário: {e}")
        return jsonify({'error': 'Erro ao registrar usuário'}), 500

@auth_api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Obter perfil do usuário logado."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
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

@auth_api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout (cliente deve remover o token)."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user:
        logger.info(f"Logout realizado para usuário: {user.email}")
    
    return jsonify({'message': 'Logout realizado com sucesso'}), 200

@auth_api_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Renovar token."""
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': new_token
    }), 200 