# app/models.py
from datetime import datetime, timezone, date
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from sqlalchemy import func
from sqlalchemy import Table  # já deve estar no topo, mas reforçando


logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    """
    Carrega um usuário pelo ID para o Flask-Login.
    """
    try:
        user = db.session.get(User, int(user_id))
        return user
    except Exception as e:
        logger.error(f"Erro ao carregar usuário {user_id} no user_loader: {e}", exc_info=True)
        return None

# ==============================================================================
# TABELAS DE ASSOCIAÇÃO
# ==============================================================================

ocorrencia_orgaos = db.Table('ocorrencia_orgaos',
    db.Column('ocorrencia_id', db.Integer, db.ForeignKey('ocorrencia.id'), primary_key=True),
    db.Column('orgao_publico_id', db.Integer, db.ForeignKey('orgao_publico.id'), primary_key=True)
)

ocorrencia_colaboradores = db.Table('ocorrencia_colaboradores',
    db.Column('ocorrencia_id', db.Integer, db.ForeignKey('ocorrencia.id'), primary_key=True),
    db.Column('colaborador_id', db.Integer, db.ForeignKey('colaborador.id'), primary_key=True)
)

# ==============================================================================
# MODELOS PRINCIPAIS
# ==============================================================================

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_supervisor = db.Column(db.Boolean, default=False, nullable=False)
    # CORREÇÃO: Adicionado timezone=True
    date_registered = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relacionamentos
    login_history = db.relationship('LoginHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    rondas_criadas = db.relationship('Ronda', backref='criador', lazy='dynamic', cascade="all, delete-orphan", foreign_keys='Ronda.user_id')
    processing_history = db.relationship('ProcessingHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    escalas_mensais = db.relationship('EscalaMensal', backref='supervisor_escala', lazy='dynamic')
    ocorrencias_registradas = db.relationship('Ocorrencia', backref='registrado_por', lazy='dynamic', foreign_keys='Ocorrencia.registrado_por_user_id')
    
    # Relações de supervisão
    ocorrencias_supervisionadas = db.relationship('Ocorrencia', backref='supervisor', lazy='dynamic', foreign_keys='Ocorrencia.supervisor_id')
    rondas_supervisionadas = db.relationship('Ronda', backref='supervisor', lazy='dynamic', foreign_keys='Ronda.supervisor_id')

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
    # CORREÇÃO: Adicionado timezone=True
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    failure_reason = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        status = "Sucesso" if self.success else f"Falha ({self.failure_reason or ''})"
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} @{self.timestamp.strftime("%Y-%m-%d %H:%M")}>'

class Colaborador(db.Model):
    __tablename__ = 'colaborador'
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False, index=True)
    cargo = db.Column(db.String(100), nullable=False, index=True)
    matricula = db.Column(db.String(50), unique=True, nullable=True, index=True)
    data_admissao = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Ativo')
    # CORREÇÃO: Adicionado timezone=True
    data_criacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_modificacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Colaborador {self.id}: {self.nome_completo}>'

class Condominio(db.Model):
    __tablename__ = 'condominio'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f'<Condominio {self.nome}>'

class Ronda(db.Model):
    __tablename__ = 'ronda'
    id = db.Column(db.Integer, primary_key=True)
    # CORREÇÃO: Adicionado timezone=True
    data_hora_inicio = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    data_hora_fim = db.Column(db.DateTime(timezone=True), nullable=True)
    log_ronda_bruto = db.Column(db.Text, nullable=False)
    relatorio_processado = db.Column(db.Text, nullable=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ronda_criador_id'), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ronda_supervisor_id'), nullable=True, index=True)
    turno_ronda = db.Column(db.String(50), nullable=True, index=True)
    escala_plantao = db.Column(db.String(100), nullable=True)
    data_plantao_ronda = db.Column(db.Date, nullable=True, index=True)
    total_rondas_no_log = db.Column(db.Integer, nullable=True, default=0)
    # CORREÇÃO: Adicionado timezone=True
    primeiro_evento_log_dt = db.Column(db.DateTime(timezone=True), nullable=True)
    ultimo_evento_log_dt = db.Column(db.DateTime(timezone=True), nullable=True)
    duracao_total_rondas_minutos = db.Column(db.Integer, default=0)

    condominio = db.relationship('Condominio', backref='rondas')

    def __repr__(self):
        supervisor_nome = self.supervisor.username if self.supervisor else "N/A"
        criador_nome = self.criador.username if self.criador else "N/A"
        return f'<Ronda {self.id} em {self.data_hora_inicio.strftime("%d/%m/%Y")}>'

class ProcessingHistory(db.Model):
    __tablename__ = 'processing_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    processing_type = db.Column(db.String(50), nullable=False, index=True)
    # CORREÇÃO: Adicionado timezone=True
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        status = "Sucesso" if self.success else "Falha"
        return f'<ProcessingHistory {self.id} ({self.processing_type}) by User {self.user_id} - {status}>'

class EscalaMensal(db.Model):
    __tablename__ = 'escala_mensal'
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False, index=True)
    nome_turno = db.Column(db.String(50), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    __table_args__ = (db.UniqueConstraint('ano', 'mes', 'nome_turno', name='_ano_mes_turno_uc'),)

    def __repr__(self):
        supervisor_nome = self.supervisor_escala.username if self.supervisor_escala else "N/A"
        return f'<EscalaMensal {self.mes}/{self.ano} - {self.nome_turno} -> {supervisor_nome}>'

class OcorrenciaTipo(db.Model):
    __tablename__ = 'ocorrencia_tipo'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descricao = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<OcorrenciaTipo {self.nome}>'

class OrgaoPublico(db.Model):
    __tablename__ = 'orgao_publico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    contato = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<OrgaoPublico {self.nome}>'

class Ocorrencia(db.Model):
    __tablename__ = 'ocorrencia'
    id = db.Column(db.Integer, primary_key=True)
    relatorio_final = db.Column(db.Text, nullable=False)
    
    # CORREÇÃO: Adicionado timezone=True
    data_hora_ocorrencia = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    turno = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Registrada', index=True)
    endereco_especifico = db.Column(db.String(255), nullable=True)
    # CORREÇÃO: Adicionado timezone=True
    data_criacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_modificacao = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), nullable=True, index=True)
    ocorrencia_tipo_id = db.Column(db.Integer, db.ForeignKey('ocorrencia_tipo.id'), nullable=False, index=True)
    registrado_por_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ocorrencia_supervisor_id'), nullable=True, index=True)

    condominio = db.relationship('Condominio', backref='ocorrencias')
    tipo = db.relationship('OcorrenciaTipo', backref='ocorrencias')
    
    orgaos_acionados = db.relationship('OrgaoPublico', secondary=ocorrencia_orgaos, lazy='subquery', backref=db.backref('ocorrencias_acionadas', lazy=True))
    colaboradores_envolvidos = db.relationship('Colaborador', secondary=ocorrencia_colaboradores, lazy='subquery', backref=db.backref('ocorrencias_atendidas', lazy=True))

    def __repr__(self):
        tipo_nome = self.tipo.nome if self.tipo else "N/A"
        data_str = self.data_hora_ocorrencia.strftime('%d/%m/%Y %H:%M')
        cond_nome = self.condominio.nome if self.condominio else "Sem Condomínio"
        return f'<Ocorrencia {self.id} - {tipo_nome} em {data_str} ({cond_nome})>'

class VWOcorrenciasDetalhadas(db.Model):
    __table__ = Table(
        'vw_ocorrencias_detalhadas',
        db.metadata,
        db.Column('id', db.Integer, primary_key=True),  # 👈 Força a chave primária
        autoload_with=db.engine
    )
