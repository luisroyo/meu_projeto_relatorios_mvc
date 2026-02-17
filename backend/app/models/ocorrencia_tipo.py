from app import db

class OcorrenciaTipo(db.Model):
    __tablename__ = "ocorrencia_tipo"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descricao = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f'<OcorrenciaTipo {self.nome}>' 