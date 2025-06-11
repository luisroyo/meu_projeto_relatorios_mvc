# app/models.py
from datetime import datetime, timezone, date # Importa date
from app import db, login_manager # Importa 'db' e 'login_manager' de app/__init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    """Carrega o usuário a partir do seu ID para a sessão do Flask-Login."""
    try:
        user = db.session.get(User, int(user_id))
        return user
    except Exception as e:
        logger.error(f"Erro ao carregar usuário {user_id} no user_loader: {e}", exc_info=True)
        return None

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    date_registered = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    login_history = db.relationship('LoginHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    rondas_criadas = db.relationship('Ronda', backref='criador', lazy='dynamic', cascade="all, delete-orphan")
    processing_history = db.relationship('ProcessingHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")

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
    attempted_username = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    failure_reason = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        status = "Sucesso" if self.success else f"Falha ({self.failure_reason or ''})"
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} Status:{status} @{self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}>'

class Ronda(db.Model):
    __tablename__ = 'ronda'
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_hora_fim = db.Column(db.DateTime, nullable=True)
    log_ronda_bruto = db.Column(db.Text, nullable=False)
    relatorio_processado = db.Column(db.Text, nullable=True)
    
    # --- ALTERAÇÃO: Adiciona ForeignKey para Condominio e novo campo 'turno_ronda' ---
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), nullable=True, index=True)
    condominio_obj = db.relationship('Condominio', backref='rondas') # Relacionamento com o modelo Condominio
    
    turno_ronda = db.Column(db.String(50), nullable=True, index=True) # Ex: 'Diurno Par', 'Noturno Ímpar'
    
    escala_plantao = db.Column(db.String(100), nullable=True) # Mantido para compatibilidade, mas turno_ronda é mais granular
    data_plantao_ronda = db.Column(db.Date, nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # Mantido como o criador/supervisor

    def __repr__(self):
        return f'<Ronda {self.id} em {self.data_hora_inicio.strftime("%Y-%m-%d %H:%M")} Cond: {self.condominio_obj.nome if self.condominio_obj else "N/A"} Turno: {self.turno_ronda or "N/A"}>'

class Colaborador(db.Model):
    __tablename__ = 'colaborador'
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False, index=True)
    cargo = db.Column(db.String(100), nullable=False, index=True)
    matricula = db.Column(db.String(50), unique=True, nullable=True, index=True)
    data_admissao = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Ativo')
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    data_modificacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Colaborador {self.id}: {self.nome_completo} ({self.cargo})>'

class Condominio(db.Model):
    __tablename__ = 'condominio'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f'<Condominio {self.nome}>'

class ProcessingHistory(db.Model):
    __tablename__ = 'processing_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    processing_type = db.Column(db.String(50), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        status = "Sucesso" if self.success else "Falha"
        return f'<ProcessingHistory {self.id} ({self.processing_type}) by User {self.user_id} - {status}>'