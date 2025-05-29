# app/models.py
from datetime import datetime, timezone
from app import db, login_manager # Importa 'db' e 'login_manager' de app/__init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    # print(f"--- DEBUG @login_manager.user_loader: Tentando carregar user_id: {user_id} ---")
    try:
        user = User.query.get(int(user_id))
        # if user:
        #     print(f"--- DEBUG @login_manager.user_loader: Usuário encontrado: ID={user.id}, Username='{user.username}', Email='{user.email}', is_admin={user.is_admin}, is_approved={user.is_approved} ---")
        # else:
        #     print(f"--- DEBUG @login_manager.user_loader: Usuário com ID {user_id} não encontrado no banco de dados. ---")
        return user
    except Exception as e:
        # print(f"--- DEBUG ERROR @login_manager.user_loader: Erro ao carregar usuário {user_id}: {e} ---")
        logger.error(f"Erro ao carregar usuário {user_id} no user_loader: {e}", exc_info=True)
        return None

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256)) # Aumentado para hashes SHA256
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    date_registered = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    login_history_entries = db.relationship('LoginHistory', backref='user_account', lazy='dynamic', cascade="all, delete-orphan") # Mudado backref para evitar conflito com user em LoginHistory
    rondas_criadas = db.relationship('Ronda', backref='criador_usuario', lazy='dynamic', cascade="all, delete-orphan") # Mudado backref para evitar conflito

    # __table_args__ = {'extend_existing': True} # Geralmente não necessário se definido corretamente

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    attempted_username = db.Column(db.String(120), nullable=False) # Aumentado para email
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    failure_reason = db.Column(db.String(100), nullable=True)

    # user = db.relationship('User', backref=db.backref('login_history_entries', lazy='dynamic')) # Removido, já definido em User

    def __repr__(self):
        status = "Sucesso" if self.success else f"Falha ({self.failure_reason or ''})"
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} Attempted:{self.attempted_username} Status:{status} @{self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}>'

class Ronda(db.Model):
    __tablename__ = 'ronda'
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_hora_fim = db.Column(db.DateTime, nullable=True)
    log_ronda_bruto = db.Column(db.Text, nullable=False)
    relatorio_processado = db.Column(db.Text, nullable=True)
    condominio = db.Column(db.String(150), nullable=True)
    escala_plantao = db.Column(db.String(100), nullable=True)
    data_plantao_ronda = db.Column(db.Date, nullable=True) # Para a data específica da ronda
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Usuário que registrou/processou
    # criador_usuario já definido pelo backref em User

    def __repr__(self):
        return f'<Ronda {self.id} em {self.data_hora_inicio.strftime("%Y-%m-%d %H:%M")}>'

# NOVO MODELO PARA COLABORADORES
class Colaborador(db.Model):
    __tablename__ = 'colaborador'
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False, index=True)
    cargo = db.Column(db.String(100), nullable=False, index=True)
    matricula = db.Column(db.String(50), unique=True, nullable=True, index=True) # Matrícula/ID do funcionário
    data_admissao = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Ativo') # Ex: Ativo, Inativo, Férias
    # Adicione outros campos que achar relevantes: setor, telefone, etc.
    
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    data_modificacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Colaborador {self.id}: {self.nome_completo} ({self.cargo})>'


class Condominio(db.Model):
    __tablename__ = 'condominio' # Opcional, mas boa prática definir o nome da tabela
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True) # Nomes únicos e indexados

    def __repr__(self):
        return f'<Condominio {self.nome}>'

# Como sua classe Ronda ficaria (mantendo 'condominio' como string):
# class Ronda(db.Model):
#     __tablename__ = 'ronda' # Exemplo de nome de tabela
#     id = db.Column(db.Integer, primary_key=True)
#     # ... outros campos da sua tabela Ronda (data_plantao, escala_plantao, log_bruto_rondas, user_id, etc.)
#     
#     condominio = db.Column(db.String(150), nullable=False) # Campo continua como string
#
#     # Se tiver uma relação com User:
#     # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     # user = db.relationship('User', backref=db.backref('rondas', lazy=True))
#
#     def __repr__(self):
#         return f'<Ronda {self.id} - {self.condominio}>'

# Certifique-se de que suas outras classes de modelo (User, LoginHistory, etc.) continuam aqui.