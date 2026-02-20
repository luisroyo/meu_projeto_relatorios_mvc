from app import db

class Condominio(db.Model):
    __tablename__ = "condominio"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False, index=True)
    whatsapp_group_id = db.Column(db.String(100), nullable=True, index=True)

    # Note: Using string references to avoid circular imports. These will be resolved by SQLAlchemy.
    # We will define the relationship in the WhatsAppMessage model.

    def __repr__(self) -> str:
        return f'<Condominio {self.nome}>'