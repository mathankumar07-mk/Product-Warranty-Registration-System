from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(db: DBSession, current_user: User = Depends(get_current_user), unread_only: bool = False):
    return notification_service.list_notifications(db, current_user, unread_only)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(notification_id: int, db: DBSession, current_user: User = Depends(get_current_user)):
    try:
        return notification_service.mark_as_read(db, notification_id, current_user)
    except LookupError as error:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/read-all", response_model=dict)
def mark_all_as_read(db: DBSession, current_user: User = Depends(get_current_user)):
    count = notification_service.mark_all_as_read(db, current_user)
    return {"marked_read": count}