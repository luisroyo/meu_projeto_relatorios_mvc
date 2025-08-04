from app import db
from sqlalchemy import func
from datetime import datetime, timezone

ocorrencia_orgaos = db.Table(
    "ocorrencia_orgaos",
    db.Column(
        "ocorrencia_id", db.Integer, db.ForeignKey("ocorrencia.id"), primary_key=True
    ),
    db.Column(
        "orgao_publico_id",
        db.Integer,
        db.ForeignKey("orgao_publico.id"),
        primary_key=True,
    ),
)

ocorrencia_colaboradores = db.Table(
    "ocorrencia_colaboradores",
    db.Column(
        "ocorrencia_id", db.Integer, db.ForeignKey("ocorrencia.id"), primary_key=True
    ),
    db.Column(
        "colaborador_id", db.Integer, db.ForeignKey("colaborador.id"), primary_key=True
    ),
)

class Ocorrencia(db.Model):
    """Modelo de ocorrência (incidente registrado)."""
    __tablename__ = "ocorrencia"
    id = db.Column(db.Integer, primary_key=True)
    relatorio_final = db.Column(db.Text, nullable=False)
    data_hora_ocorrencia = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    turno = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Registrada", index=True)
    endereco_especifico = db.Column(db.String(255), nullable=True)
    logradouro_id = db.Column(db.Integer, db.ForeignKey("logradouro.id"), nullable=True)
    logradouro = db.relationship("Logradouro", backref="ocorrencias")
    data_criacao = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    data_modificacao = db.Column(
        db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )
    condominio_id = db.Column(
        db.Integer, db.ForeignKey("condominio.id"), nullable=True, index=True
    )
    ocorrencia_tipo_id = db.Column(
        db.Integer, db.ForeignKey("ocorrencia_tipo.id"), nullable=False, index=True
    )
    registrado_por_user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    supervisor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_ocorrencia_supervisor_id"),
        nullable=True,
        index=True,
    )
    condominio = db.relationship("Condominio", backref="ocorrencias")
    tipo = db.relationship("OcorrenciaTipo", backref="ocorrencias")
    registrado_por = db.relationship("User", foreign_keys=[registrado_por_user_id])
    supervisor = db.relationship("User", foreign_keys=[supervisor_id])

    orgaos_acionados = db.relationship(
        "OrgaoPublico",
        secondary=ocorrencia_orgaos,
        lazy="subquery",
        backref=db.backref("ocorrencias_acionadas", lazy=True),
    )
    colaboradores_envolvidos = db.relationship(
        "Colaborador",
        secondary=ocorrencia_colaboradores,
        lazy="subquery",
        backref=db.backref("ocorrencias_atendidas", lazy=True),
    )

    def __repr__(self) -> str:
        tipo_nome = self.tipo.nome if self.tipo else "N/A"
        data_str = self.data_hora_ocorrencia.strftime('%d/%m/%Y %H:%M')
        cond_nome = self.condominio.nome if self.condominio else "Sem Condomínio"
        return f'<Ocorrencia {self.id} - {tipo_nome} em {data_str} ({cond_nome})>'

__all__ = ["Ocorrencia", "ocorrencia_orgaos", "ocorrencia_colaboradores"]