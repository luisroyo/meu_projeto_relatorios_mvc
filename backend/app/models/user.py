from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_supervisor = db.Column(db.Boolean, default=False, nullable=False)
    date_registered = db.Column(
        db.DateTime(timezone=True), default=db.func.now()
    )
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relacionamentos
    login_history = db.relationship(
        "LoginHistory", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    rondas_criadas = db.relationship(
        "Ronda",
        lazy="dynamic",
        cascade="all, delete-orphan",
        foreign_keys="Ronda.user_id",
        back_populates="criador"
    )
    processing_history = db.relationship(
        "ProcessingHistory",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    escalas_mensais = db.relationship(
        "EscalaMensal", backref="supervisor_escala", lazy="dynamic"
    )
    ocorrencias_registradas = db.relationship(
        "Ocorrencia",
        lazy="dynamic",
        foreign_keys="Ocorrencia.registrado_por_user_id",
        back_populates="registrado_por"
    )

    # Relações de supervisão
    ocorrencias_supervisionadas = db.relationship(
        "Ocorrencia",
        lazy="dynamic",
        foreign_keys="Ocorrencia.supervisor_id",
        back_populates="supervisor"
    )
    rondas_supervisionadas = db.relationship(
        "Ronda",
        lazy="dynamic",
        foreign_keys="Ronda.supervisor_id",
        back_populates="supervisor"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>' 