from app import db
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from .user import User

class UserOnline(db.Model):
    """Modelo para rastrear usuários online."""
    __tablename__ = "user_online"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False, unique=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 pode ter até 45 caracteres
    user_agent = db.Column(db.Text, nullable=True)
    last_activity = db.Column(db.DateTime(timezone=True), default=db.func.now())
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())
    
    # Relacionamento com User
    user = db.relationship('User', backref='online_sessions')
    
    @classmethod
    def get_online_users(cls, minutes_threshold=15):
        """Retorna usuários que estiveram ativos nos últimos X minutos."""
        threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_threshold)
        return cls.query.filter(
            cls.last_activity >= threshold
        ).join(User).with_entities(
            User.id,
            User.username,
            User.email,
            func.max(cls.last_activity).label('last_activity')
        ).group_by(
            User.id,
            User.username,
            User.email
        ).order_by(
            func.max(cls.last_activity).desc()
        ).all()
    
    @classmethod
    def cleanup_old_sessions(cls, minutes_threshold=30):
        """Remove sessões antigas."""
        threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_threshold)
        cls.query.filter(cls.last_activity < threshold).delete()
        db.session.commit()
    
    @classmethod
    def update_activity(cls, user_id, session_id, ip_address=None, user_agent=None):
        """Atualiza ou cria uma sessão de usuário online."""
        try:
            session = cls.query.filter_by(session_id=session_id).first()
            
            if session:
                # Atualiza sessão existente
                session.last_activity = datetime.now(timezone.utc)
                if ip_address:
                    session.ip_address = ip_address
                if user_agent:
                    session.user_agent = user_agent
            else:
                # Cria nova sessão
                session = cls(
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    last_activity=datetime.now(timezone.utc)
                )
                db.session.add(session)
            
            db.session.commit()
            return session
        except Exception as e:
            db.session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao atualizar atividade do usuário {user_id}: {e}")
            raise
    
    @classmethod
    def remove_session(cls, session_id):
        """Remove uma sessão específica."""
        session = cls.query.filter_by(session_id=session_id).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False 