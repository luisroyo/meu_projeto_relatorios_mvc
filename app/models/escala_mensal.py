from app import db

class EscalaMensal(db.Model):
    __tablename__ = "escala_mensal"
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False, index=True)
    nome_turno = db.Column(db.String(50), nullable=False, index=True)
    supervisor_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    __table_args__ = (
        db.UniqueConstraint("ano", "mes", "nome_turno", name="uq_escala_mes_turno"),
    )

    @property
    def supervisor(self):
        from .user import User
        return User.query.get(self.supervisor_id)

    def __repr__(self) -> str:
        return f'<EscalaMensal {self.ano}-{self.mes} {self.nome_turno}>' 