"""
APIs de autenticação usando JWT.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.models.login_history import LoginHistory
from app import db
from datetime import datetime, timezone
import logging
from app.blueprints.api.utils import success_response, error_response
from app import limiter

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

def _registrar_login_api(user, sucesso, req, motivo_falha=None):
    """Registra tentativa de login no histórico para API."""
    try:
        log = LoginHistory(
            user_id=user.id if user else None,
            attempted_username=req.get_json().get("email") or req.get_json().get("username") if req.is_json else req.form.get("email") or req.form.get("username"),
            timestamp=datetime.now(timezone.utc),
            success=sucesso,
            ip_address=req.remote_addr,
            user_agent=req.user_agent.string,
            failure_reason=motivo_falha,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao registrar tentativa de login na API: {e}")

@auth_api_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Endpoint de login que retorna JWT token."""
    data = request.get_json()
    
    if not data or not data.get('password'):
        return error_response('Senha é obrigatória', status_code=400)
    
    login_identifier = data.get('email') or data.get('username')
    
    if not login_identifier:
        return error_response('Email ou Username é obrigatório', status_code=400)
    
    # Tenta buscar por email primeiro, depois por username
    user = User.query.filter((User.email == login_identifier) | (User.username == login_identifier)).first()
    login_success = False
    
    if user and user.check_password(data['password']):
        if not user.is_approved:
            _registrar_login_api(user, False, request, "Account not approved")
            return error_response('Usuário não aprovado', status_code=403)
        
        # Atualiza last_login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        login_success = True
        
        # Registra login bem-sucedido
        _registrar_login_api(user, True, request, None)
        
        logger.info(f"Login bem-sucedido para usuário: {user.email}")
        
        return success_response(
            data={
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'is_supervisor': user.is_supervisor,
                    'is_approved': user.is_approved
                }
            },
            message='Login realizado com sucesso'
        )
    
    # Registra tentativa falhada
    _registrar_login_api(user, False, request, "Credenciais inválidas")
    logger.warning(f"Tentativa de login falhou para email: {data.get('email')}")
    return error_response('Credenciais inválidas', status_code=401)

@auth_api_bp.route('/register', methods=['POST'])
def register():
    """Endpoint de registro de usuário."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return error_response('Email, senha e username são obrigatórios', status_code=400)
    
    # Verificar se usuário já existe
    if User.query.filter_by(email=data['email']).first():
        return error_response('Email já cadastrado', status_code=409)
    
    if User.query.filter_by(username=data['username']).first():
        return error_response('Username já cadastrado', status_code=409)
    
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
        return success_response(
            data={'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'is_approved': new_user.is_approved
            }},
            message='Usuário registrado com sucesso. Aguarde aprovação do administrador.'
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao registrar usuário: {e}")
        return error_response('Erro interno ao registrar usuário', status_code=500)

@auth_api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Obter perfil do usuário logado."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('Usuário não encontrado', status_code=404)
        
        return success_response(
            data={
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_supervisor': user.is_supervisor,
                'is_approved': user.is_approved,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            message='Perfil obtido com sucesso'
        )
    except Exception as e:
        logger.error(f"Erro ao obter perfil: {e}")
        return error_response('Erro interno ao obter perfil', status_code=500)

@auth_api_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout do usuário."""
    try:
        # Em JWT, o logout é feito no frontend removendo o token
        # Aqui podemos registrar o logout no histórico se necessário
        logger.info(f"Logout realizado para usuário ID: {get_jwt_identity()}")
        return success_response(message='Logout realizado com sucesso')
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return error_response('Erro interno no logout', status_code=500)

@auth_api_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Renovar token JWT."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('Usuário não encontrado', status_code=404)
        
        # Criar novo token
        new_token = create_access_token(identity=user.id)
        
        return success_response(
            data={'access_token': new_token},
            message='Token renovado com sucesso'
        )
    except Exception as e:
        logger.error(f"Erro ao renovar token: {e}")
        return error_response('Erro interno ao renovar token', status_code=500) 