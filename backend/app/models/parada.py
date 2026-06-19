from app import db
from datetime import datetime, timezone

class Parada(db.Model):
    """Modelo de registro de parada (ponto fixo / estacionado)."""
    __tablename__ = "parada"
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    data_hora_fim = db.Column(db.DateTime(timezone=True), nullable=True)
    log_parada_bruto = db.Column(db.Text, nullable=False)
    relatorio_processado = db.Column(db.Text, nullable=True)
    condominio_id = db.Column(
        db.Integer, db.ForeignKey("condominio.id"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_parada_criador_id"),
        nullable=False,
        index=True,
    )
    supervisor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_parada_supervisor_id"),
        nullable=True,
        index=True,
    )
    turno_parada = db.Column(db.String(50), nullable=True, index=True)
    escala_plantao = db.Column(db.String(100), nullable=True)
    data_plantao_parada = db.Column(db.Date, nullable=True, index=True)
    total_paradas_no_log = db.Column(db.Integer, nullable=True, default=0)
    primeiro_evento_log_dt = db.Column(db.DateTime(timezone=True), nullable=True)
    ultimo_evento_log_dt = db.Column(db.DateTime(timezone=True), nullable=True)
    duracao_total_paradas_minutos = db.Column(db.Integer, default=0)
    tipo = db.Column(db.String(50), nullable=True, default="tradicional")  # tradicional, esporadica

    condominio = db.relationship("Condominio", backref="paradas")
    
    # Relacionamentos com User (criador e supervisor)
    criador = db.relationship("User", foreign_keys=[user_id], back_populates="paradas_criadas")
    supervisor = db.relationship("User", foreign_keys=[supervisor_id], back_populates="paradas_supervisionadas")

    def __repr__(self) -> str:
        return f'<Parada {self.id} - {self.data_plantao_parada}>'
