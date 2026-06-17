from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.notification as notification_crud
import api.schemas.notification as notification_schema

router = APIRouter()


@router.get("/notification/unread-count", response_model=notification_schema.UnreadCount)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await notification_crud.get_unread_count(db, firebase_user["uid"])


@router.get("/notification", response_model=List[notification_schema.NotificationSummary])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await notification_crud.get_notifications(db, firebase_user["uid"])


@router.get("/notification/{notification_id}", response_model=notification_schema.NotificationDetail)
async def get_notification_detail(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await notification_crud.get_notification_detail(
        db,
        notification_id,
        firebase_user["uid"],
    )

@router.post("/notification/{notification_id}/reply")
async def reply_notification(
    notification_id: int,
    request: notification_schema.NotificationReplyRequest,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await notification_crud.reply_notification(
        db,
        notification_id,
        firebase_user["uid"],
        request.message,
    )


@router.post("/notification/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await notification_crud.dismiss_notification(
        db,
        notification_id,
        firebase_user["uid"],
    )