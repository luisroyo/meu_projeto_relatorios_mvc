from app import db

class Logradouro(db.Model):
    __tablename__ = "logradouro"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Logradouro {self.nome}>" 