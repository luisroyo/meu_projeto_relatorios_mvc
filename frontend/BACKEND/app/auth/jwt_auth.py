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
    print(f"JWT_SECRET_KEY configurada: {app.config['JWT_SECRET_KEY'][:10]}...")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    # Desabilitar CSRF para tokens JWT
    app.config['JWT_CSRF_CHECK_FORM'] = False
    app.config['JWT_CSRF_IN_COOKIES'] = False
    app.config['JWT_CSRF_IN_COOKIES'] = False
    app.config['JWT_CSRF_CHECK_FORM'] = False
    app.config['JWT_CSRF_METHODS'] = []
    app.config['JWT_CSRF_HEADER_NAME'] = None
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    """Define como o ID do usuário é armazenado no token."""
    # Se user já é um int (ID), retorna como string
    if isinstance(user, int):
        return str(user)
    # Se user é um objeto User, retorna o ID como string
    return str(user.id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Define como o usuário é recuperado do token."""
    from app.models.user import User
    identity = jwt_data["sub"]
    # Converter string de volta para int
    user_id = int(identity)
    return User.query.filter_by(id=user_id).one_or_none()

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Callback para token expirado."""
    return {"error": "Token expirado", "code": "token_expired"}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Callback para token inválido."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Token inválido: {error}")
    logger.error(f"Tipo de erro: {type(error)}")
    logger.error(f"Detalhes completos: {str(error)}")
    return {"error": f"Token inválido: {error}", "code": "invalid_token"}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Callback para token não fornecido."""
    return {"error": "Token não fornecido", "code": "missing_token"}, 401 