from datetime import datetime, timezone
from app import db, login_manager # Importa 'db' e 'login_manager' de app/__init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging # Adicione esta importação para o logger do módulo

logger = logging.getLogger(__name__) # Logger para este módulo

# Função user_loader para o Flask-Login: diz como carregar um usuário dado o ID.
@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Tentando carregar usuário com ID: {user_id}")
    try:
        user = db.session.get(User, int(user_id))
        if user:
            logger.debug(f"Usuário {user.username} carregado com sucesso.")
        else:
            logger.warning(f"Nenhum usuário encontrado com ID: {user_id}")
        return user
    except Exception as e:
        logger.error(f"Erro ao carregar usuário ID {user_id}: {e}", exc_info=True)
        return None


class User(db.Model, UserMixin):
    __tablename__ = 'user' 

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True) # Adicionado index
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) # Adicionado index
    password_hash = db.Column(db.String(256), nullable=False) 
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)) 
    is_admin = db.Column(db.Boolean, nullable=False, default=False) 

    login_history = db.relationship('LoginHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan") # Alterado para lazy='dynamic'

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        logger.info(f"Hash de senha definido para o usuário: {self.username}")

    def check_password(self, password):
        result = check_password_hash(self.password_hash, password)
        logger.debug(f"Verificação de senha para {self.username}: {'Sucesso' if result else 'Falha'}")
        return result

class LoginHistory(db.Model):
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True) # Adicionado index
    attempted_username = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True) # Adicionado index
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True) 
    user_agent = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        status = "Sucesso" if self.success else "Falha"
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} Attempted:{self.attempted_username} Status:{status} @{self.timestamp}>'