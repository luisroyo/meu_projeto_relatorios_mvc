from datetime import datetime, timezone, date
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
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
    is_supervisor = db.Column(db.Boolean, default=False, nullable=False)
    date_registered = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    login_history = db.relationship('LoginHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    rondas_criadas = db.relationship('Ronda', backref='criador', lazy='dynamic', cascade="all, delete-orphan", foreign_keys='Ronda.user_id')
    processing_history = db.relationship('ProcessingHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    rondas_supervisionadas = db.relationship(
        'Ronda',
        backref='supervisor',
        lazy='dynamic',
        cascade="all, delete-orphan",
        primaryjoin="User.id == Ronda.supervisor_id"
    )

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

class Ronda(db.Model):
    __tablename__ = 'ronda'
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_hora_fim = db.Column(db.DateTime, nullable=True)

    log_ronda_bruto = db.Column(db.Text, nullable=False)
    relatorio_processado = db.Column(db.Text, nullable=True)

    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), nullable=True, index=True)
    condominio_obj = db.relationship('Condominio', backref='rondas')

    turno_ronda = db.Column(db.String(50), nullable=True, index=True)
    escala_plantao = db.Column(db.String(100), nullable=True)
    data_plantao_ronda = db.Column(db.Date, nullable=True, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ronda_criador_id'), nullable=False, index=True)

    total_rondas_no_log = db.Column(db.Integer, nullable=True, default=0)
    primeiro_evento_log_dt = db.Column(db.DateTime, nullable=True)
    ultimo_evento_log_dt = db.Column(db.DateTime, nullable=True)

    duracao_total_rondas_minutos = db.Column(db.Integer, default=0)

    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ronda_supervisor_id'), nullable=True, index=True)

    is_incomplete = db.Column(db.Boolean, default=False, nullable=False)
    is_duration_anomalous = db.Column(db.Boolean, default=False, nullable=False)

    # Relacionamento com RondaSegmento
    ronda_segments = db.relationship('RondaSegmento', backref='parent_ronda', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        supervisor_nome = self.supervisor.username if self.supervisor else "N/A"
        criador_nome = self.criador.username if self.criador else "N/A"
        return (
            f'<Ronda {self.id} em {self.data_hora_inicio.strftime("%Y-%m-%d %H:%M")} '
            f'Cond: {self.condominio_obj.nome if self.condominio_obj else "N/A"} '
            f'Turno: {self.turno_ronda or "N/A"} '
            f'Criador: {criador_nome} '
            f'Supervisor: {supervisor_nome} '
            f'Total Rondas: {self.total_rondas_no_log or 0}>'
        )

class RondaSegmento(db.Model):
    __tablename__ = 'ronda_segmento'
    id = db.Column(db.Integer, primary_key=True)
    
    ronda_id = db.Column(db.Integer, db.ForeignKey('ronda.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Detalhes do segmento individual da ronda - AGORA NULÁVEIS
    inicio_dt = db.Column(db.DateTime, nullable=True) # ALTERADO para nullable=True
    termino_dt = db.Column(db.DateTime, nullable=True)
    duracao_minutos = db.Column(db.Integer, nullable=False)
    vtr = db.Column(db.String(50), nullable=True) # Viatura associada ao segmento

    # Flags de qualidade específicas para o segmento
    is_incomplete_segment = db.Column(db.Boolean, default=False, nullable=False)
    is_duration_anomalous_segment = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return (
            f'<RondaSegmento {self.id} (Ronda:{self.ronda_id}) '
            f'VTR:{self.vtr} Início:{self.inicio_dt.strftime("%H:%M") if self.inicio_dt else "N/A"} '
            f'Duração:{self.duracao_minutos}min>'
        )

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
    
class EscalaMensal(db.Model):
    __tablename__ = 'escala_mensal'
    id = db.Column(db.Integer, primary_key=True)
    
    # Ano e Mês da escala
    ano = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False, index=True)

    # Ex: 'Noturno Par', 'Diurno Impar', etc.
    nome_turno = db.Column(db.String(50), nullable=False, index=True)
    
    # Chave estrangeira para o usuário que é o supervisor daquele turno naquele mês/ano
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Relacionamento para acessar o objeto User facilmente
    supervisor = db.relationship('User', backref='escalas_mensais')

    # Garante que não haja duas atribuições para o mesmo turno no mesmo mês/ano
    __table_args__ = (db.UniqueConstraint('ano', 'mes', 'nome_turno', name='_ano_mes_turno_uc'),)

    def __repr__(self):
        supervisor_nome = self.supervisor.username if self.supervisor else "N/A"
        return f'<EscalaMensal {self.mes}/{self.ano} - {self.nome_turno} -> {supervisor_nome}>'