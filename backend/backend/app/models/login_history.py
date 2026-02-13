from app import db
from datetime import datetime, timezone

class LoginHistory(db.Model):
    __tablename__ = "login_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    attempted_username = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    failure_reason = db.Column(db.String(100), nullable=True)

    def __repr__(self) -> str:
        status = "Sucesso" if self.success else f"Falha ({self.failure_reason or ''})"
        return f'<LoginHistory ID:{self.id} UserID:{self.user_id or "N/A"} @{self.timestamp.strftime("%Y-%m-%d %H:%M")}> ' 