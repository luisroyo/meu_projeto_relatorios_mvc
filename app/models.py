from datetime import datetime, timezone, date
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    """
    Carrega um usuário pelo ID para o Flask-Login.
    """
    try:
        # Usa db.session.get que é otimizado para buscar por chave primária.
        user = db.session.get(User, int(user_id))
        return user
    except Exception as e:
        logger.error(f"Erro ao carregar usuário {user_id} no user_loader: {e}", exc_info=True)
        return None

# ==============================================================================
# MODELOS EXISTENTES
# ==============================================================================

class User(UserMixin, db.Model):
    """
    Modelo para os usuários do sistema.
    """
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

    # Relacionamentos
    login_history = db.relationship('LoginHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    rondas_criadas = db.relationship('Ronda', backref='criador', lazy='dynamic', cascade="all, delete-orphan", foreign_keys='Ronda.user_id')
    processing_history = db.relationship('ProcessingHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    escalas_mensais = db.relationship('EscalaMensal', backref='supervisor', lazy='dynamic')
    ocorrencias_registradas = db.relationship('Ocorrencia', backref='registrado_por', lazy='dynamic', foreign_keys='Ocorrencia.registrado_por_user_id') # <<< ALTERAÇÃO: Adicionado foreign_keys para clareza

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
    """
    Modelo para registrar o histórico de tentativas de login.
    """
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
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} @{self.timestamp.strftime("%Y-%m-%d %H:%M")}>'

class Colaborador(db.Model):
    """
    Modelo para os colaboradores (funcionários).
    """
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
        return f'<Colaborador {self.id}: {self.nome_completo}>'

class Condominio(db.Model):
    """
    Modelo para os condomínios onde as rondas ocorrem.
    """
    __tablename__ = 'condominio'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f'<Condominio {self.nome}>'

class Ronda(db.Model):
    """
    Modelo para registrar cada ronda realizada.
    """
    __tablename__ = 'ronda'
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_hora_fim = db.Column(db.DateTime, nullable=True)
    log_ronda_bruto = db.Column(db.Text, nullable=False)
    relatorio_processado = db.Column(db.Text, nullable=True)
    
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominio.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ronda_criador_id'), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ronda_supervisor_id'), nullable=True, index=True)
    
    turno_ronda = db.Column(db.String(50), nullable=True, index=True)
    escala_plantao = db.Column(db.String(100), nullable=True)
    data_plantao_ronda = db.Column(db.Date, nullable=True, index=True)
    
    total_rondas_no_log = db.Column(db.Integer, nullable=True, default=0)
    primeiro_evento_log_dt = db.Column(db.DateTime, nullable=True)
    ultimo_evento_log_dt = db.Column(db.DateTime, nullable=True)
    duracao_total_rondas_minutos = db.Column(db.Integer, default=0)
    
    condominio_obj = db.relationship('Condominio', backref='rondas')

    def __repr__(self):
        supervisor_nome = self.supervisor.username if self.supervisor else "N/A"
        criador_nome = self.criador.username if self.criador else "N/A"
        return f'<Ronda {self.id} em {self.data_hora_inicio.strftime("%d/%m/%Y")}>'

class ProcessingHistory(db.Model):
    """
    Modelo para auditar processos automáticos do sistema.
    """
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
    """
    Modelo para gerenciar as escalas mensais de trabalho dos supervisores.
    """
    __tablename__ = 'escala_mensal'
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False, index=True)
    nome_turno = db.Column(db.String(50), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    __table_args__ = (db.UniqueConstraint('ano', 'mes', 'nome_turno', name='_ano_mes_turno_uc'),)

    def __repr__(self):
        supervisor_nome = self.supervisor.username if self.supervisor else "N/A"
        return f'<EscalaMensal {self.mes}/{self.ano} - {self.nome_turno} -> {supervisor_nome}>'

# ==============================================================================
# NOVOS MODELOS PARA O SISTEMA DE OCORRÊNCIAS
# ==============================================================================

class OcorrenciaTipo(db.Model):
    """
    Cadastro dinâmico para os tipos de ocorrência (Ex: 'Furto', 'Vandalismo').
    """
    __tablename__ = 'ocorrencia_tipo'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descricao = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<OcorrenciaTipo {self.nome}>'

class OrgaoPublico(db.Model):
    """
    Cadastro dinâmico para os órgãos públicos acionados (Ex: 'Polícia Militar', 'SAMU').
    """
    __tablename__ = 'orgao_publico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    contato = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<OrgaoPublico {self.nome}>'

# Tabela de associação para o relacionamento Many-to-Many entre Ocorrência e Órgão Público.
ocorrencia_orgaos = db.Table('ocorrencia_orgaos',
    db.Column('ocorrencia_id', db.Integer, db.ForeignKey('ocorrencia.id'), primary_key=True),
    db.Column('orgao_publico_id', db.Integer, db.ForeignKey('orgao_publico.id'), primary_key=True)
)

# <<< ALTERAÇÃO: Nova tabela de associação para Ocorrência e Colaborador >>>
ocorrencia_colaboradores = db.Table('ocorrencia_colaboradores',
    db.Column('ocorrencia_id', db.Integer, db.ForeignKey('ocorrencia.id'), primary_key=True),
    db.Column('colaborador_id', db.Integer, db.ForeignKey('colaborador.id'), primary_key=True)
)

class Ocorrencia(db.Model):
    """
    # <<< ALTERAÇÃO: Docstring atualizada para refletir a independência das rondas.
    Modelo principal para registrar uma ocorrência oficial.
    """
    __tablename__ = 'ocorrencia'
    id = db.Column(db.Integer, primary_key=True)

    # <<< ALTERAÇÃO: O vínculo com a Ronda foi REMOVIDO daqui.
    # ronda_id = db.Column(db.Integer, db.ForeignKey('ronda.id'), unique=True, nullable=False, index=True)
    
    relatorio_final = db.Column(db.Text, nullable=False)
    
    data_ocorrencia = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    status = db.Column(db.String(50), nullable=False, default='Registrada', index=True)
    endereco_especifico = db.Column(db.String(255), nullable=True)

    ocorrencia_tipo_id = db.Column(db.Integer, db.ForeignKey('ocorrencia_tipo.id'), nullable=False, index=True)
    registrado_por_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # <<< ALTERAÇÃO: O relacionamento com Ronda foi REMOVIDO.
    # ronda = db.relationship('Ronda', backref=db.backref('ocorrencia', uselist=False))
    
    tipo = db.relationship('OcorrenciaTipo', backref='ocorrencias')
    
    # Relacionamento Many-to-Many com OrgaoPublico (permanece igual)
    orgaos_acionados = db.relationship('OrgaoPublico', secondary=ocorrencia_orgaos, lazy='subquery',
                                       backref=db.backref('ocorrencias', lazy=True))

    # <<< ALTERAÇÃO: Novo relacionamento Many-to-Many com Colaborador >>>
    colaboradores_envolvidos = db.relationship('Colaborador', secondary=ocorrencia_colaboradores, lazy='subquery',
                                               backref=db.backref('ocorrencias_atendidas', lazy=True))

    def __repr__(self):
        tipo_nome = self.tipo.nome if self.tipo else "N/A"
        data_str = self.data_ocorrencia.strftime('%d/%m/%Y')
        return f'<Ocorrencia {self.id} - {tipo_nome} em {data_str}>'