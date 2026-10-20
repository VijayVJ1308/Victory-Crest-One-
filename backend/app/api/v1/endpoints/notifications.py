"""Victory Crest One - Notification Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from backend.app.schemas.master_data import NotificationOut
from backend.app.services.master_data_service import notification_service
from backend.app.core.permissions import get_current_user

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])


@router.get(
    "",
    response_model=List[NotificationOut],
    summary="List Notifications",
    description="Returns notifications for the authenticated user and organization."
)
def list_notifications(
    is_read: Optional[bool] = Query(None),
    user: dict = Depends(get_current_user)
):
    return notification_service.list_notifications(is_read=is_read)


@router.get(
    "/unread-count",
    summary="Get Unread Notification Count"
)
def get_unread_count(user: dict = Depends(get_current_user)):
    return {"unread_count": notification_service.unread_count()}


@router.post(
    "/{notification_id}/read",
    summary="Mark Notification as Read"
)
def mark_as_read(notification_id: str, user: dict = Depends(get_current_user)):
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "id": notification_id}
