from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.notification import NotificationCreate


def create_notification(db: Session, data: NotificationCreate) -> Notification:
    notification = Notification(**data.model_dump())
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def create_user_notification(db: Session, user_id: int, type: NotificationType, title: str, message: str) -> Notification:
    return create_notification(db, NotificationCreate(user_id=user_id, type=type, title=title, message=message))


def get_notification(db: Session, notification_id: int, user: User) -> Notification:
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if not notification:
        raise LookupError("Notification not found")
    return notification


def list_notifications(db: Session, user: User, unread_only: bool = False) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read == 0)
    return query.order_by(Notification.created_at.desc()).all()


def mark_as_read(db: Session, notification_id: int, user: User) -> Notification:
    notification = get_notification(db, notification_id, user)
    notification.is_read = 1
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user: User) -> int:
    count = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == 0).update({Notification.is_read: 1})
    db.commit()
    return count