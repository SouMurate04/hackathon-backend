from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model


async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    return result.scalars().first()


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    item_id: int | None = None,
):
    notification = model.Notification(
        user_id=user_id,
        item_id=item_id,
        title=title,
        message=message,
        timestamp=datetime.now(),
        is_read=False,
    )

    db.add(notification)
    return notification


async def get_unread_count(db: AsyncSession, firebase_uid: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(func.count(model.Notification.id)).where(
            model.Notification.user_id == user.id,
            model.Notification.is_read == False,
        )
    )

    return {"unread_count": result.scalar_one()}


async def get_notifications(db: AsyncSession, firebase_uid: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(
            model.Notification.id.label("id"),
            model.Notification.title.label("title"),
            model.Notification.timestamp.label("timestamp"),
            model.Notification.is_read.label("is_read"),
            model.Notification.item_id.label("item_id"),
        )
        .where(model.Notification.user_id == user.id)
        .order_by(model.Notification.timestamp.desc())
    )

    return result.mappings().all()


async def get_notification_detail(
    db: AsyncSession,
    notification_id: int,
    firebase_uid: str,
):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(model.Notification).where(
            model.Notification.id == notification_id,
            model.Notification.user_id == user.id,
        )
    )
    notification = result.scalars().first()

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True

    data = {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "timestamp": notification.timestamp,
        "is_read": True,
        "item_id": notification.item_id,
    }

    await db.commit()

    return data