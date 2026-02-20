from app import db
from datetime import datetime, timezone

class WhatsAppMessage(db.Model):
    """Modelo para armazenar mensagens recebidas do WhatsApp vinculadas a um Condomínio."""
    __tablename__ = "whatsapp_message"
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(150), unique=True, nullable=False, index=True)
    condominio_id = db.Column(
        db.Integer, 
        db.ForeignKey("condominio.id", name="fk_whatsapp_msg_condominio_id"), 
        nullable=False, 
        index=True
    )
    remote_jid = db.Column(db.String(100), nullable=False) # ID do grupo no WhatsApp
    participant_jid = db.Column(db.String(100), nullable=False) # Número de quem enviou
    push_name = db.Column(db.String(150), nullable=True) # Nome salvo de quem enviou
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    
    # Campo para indicar se essa mensagem já foi parseada/processada e vinculada a uma Ronda
    # Isso pode ser útil para não re-processar eternamente, mas num primeiro momento 
    # faremos a busca por intervalo de tempo independentemente.
    is_processed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    condominio = db.relationship("Condominio", backref=db.backref("whatsapp_messages", lazy=True))

    def __repr__(self) -> str:
        return f'<WhatsAppMessage {self.id} - {self.push_name} @ {self.timestamp}>'
