"""
Configuração JWT para autenticação da API.
"""
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
# Importação movida para dentro das funções para evitar circular import

jwt = JWTManager()

def init_jwt(app):
    """Inicializa a configuração JWT na aplicação Flask."""
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    """Define como o ID do usuário é armazenado no token."""
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Define como o usuário é recuperado do token."""
    from app.models.user import User
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Callback para token expirado."""
    return {"error": "Token expirado", "code": "token_expired"}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Callback para token inválido."""
    return {"error": "Token inválido", "code": "invalid_token"}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Callback para token não fornecido."""
    return {"error": "Token não fornecido", "code": "missing_token"}, 401 