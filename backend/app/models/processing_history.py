from app import db
from datetime import datetime, timezone

class ProcessingHistory(db.Model):
    __tablename__ = "processing_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    processing_type = db.Column(db.String(50), nullable=False, index=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f'<ProcessingHistory {self.id}>' 