from app import db
from datetime import datetime

class GeminiUsageLog(db.Model):
    """Log de uso das APIs do Gemini."""
    __tablename__ = 'gemini_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)  # Para casos onde user_id não está disponível
    api_key_name = db.Column(db.String(50), nullable=False)  # GOOGLE_API_KEY_1, GOOGLE_API_KEY_2
    service_name = db.Column(db.String(100), nullable=False)  # PatrimonialReportService, etc.
    prompt_length = db.Column(db.Integer, nullable=True)
    response_length = db.Column(db.Integer, nullable=True)
    cache_hit = db.Column(db.Boolean, default=False)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com usuário
    user = db.relationship('User', backref='gemini_usage_logs')
    
    def __repr__(self):
        return f'<GeminiUsageLog {self.id}: {self.username} - {self.api_key_name} - {self.created_at}>' 