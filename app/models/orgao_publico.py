from app import db

class OrgaoPublico(db.Model):
    __tablename__ = "orgao_publico"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    contato = db.Column(db.String(100), nullable=True)

    def __repr__(self) -> str:
        return f'<OrgaoPublico {self.nome}>' 