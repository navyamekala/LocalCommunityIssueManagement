"""
In-App Notification Service for Citizen Updates and Administrative Alerts.
"""

from sqlalchemy.orm import Session
from ..models.models import Notification


def create_notification(db: Session, user_id: int, message: str, complaint_id: int = None) -> Notification:
    """Creates and persists an in-app notification for a given user."""
    notif = Notification(
        user_id=user_id,
        complaint_id=complaint_id,
        message=message,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
