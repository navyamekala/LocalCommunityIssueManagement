"""
In-App Notifications Router for Logged-In Users.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.models import Notification, User
from ..schemas.schemas import NotificationOut
from .auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationOut])
def get_user_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns all notifications for the authenticated user ordered by most recent."""
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(30).all()


@router.put("/{id}/read")
def mark_notification_as_read(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Marks a single notification as read."""
    notif = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read", "id": id}


@router.put("/read-all/mark")
def mark_all_notifications_as_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Marks all notifications for the authenticated user as read."""
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
