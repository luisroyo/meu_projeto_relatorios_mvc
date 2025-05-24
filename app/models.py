from datetime import datetime, timezone
from app import db, login_manager # Importa 'db' e 'login_manager' de app/__init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging # Adicione esta importação para o logger do módulo


logger = logging.getLogger(__name__) # Logger para este módulo

# Função user_loader para o Flask-Login: diz como carregar um usuário dado o ID.
@login_manager.user_loader
def load_user(user_id):
    # Adicione logs aqui para depuração
    print(f"--- DEBUG: load_user chamado com user_id: {user_id} ---")
    user = User.query.get(int(user_id))
    if user:
        print(f"--- DEBUG: Usuário encontrado: {user.username}, is_admin: {user.is_admin}, is_approved: {user.is_approved} ---")
    else:
        print(f"--- DEBUG: Usuário com id {user_id} não encontrado. ---")
    return user

class Ronda(db.Model):
    __tablename__ = 'ronda' # Boa prática
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Exemplo de campo
    log_ronda = db.Column(db.Text, nullable=False) # Exemplo de campo
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Chave estrangeira para a tabela 'user'

    def __repr__(self):
        return f'<Ronda {self.id}>'
    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    rondas = db.relationship('Ronda', backref='author', lazy='dynamic')

    # Campos adicionados anteriormente
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # ADICIONE ESTA LINHA:
    __table_args__ = {'extend_existing': True}

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class LoginHistory(db.Model):
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True) # Adicionado index
    attempted_username = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True) # Adicionado index
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    failure_reason = db.Column(db.String(100), nullable=True) # << ADICIONE ESTA LINHA

    user = db.relationship('User', backref=db.backref('login_history_entries', lazy='dynamic'))

    def __repr__(self):
        status = "Sucesso" if self.success else "Falha"
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} Attempted:{self.attempted_username} Status:{status} @{self.timestamp}>'