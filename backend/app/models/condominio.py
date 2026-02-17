from app import db

class Condominio(db.Model):
    __tablename__ = "condominio"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f'<Condominio {self.nome}>' 