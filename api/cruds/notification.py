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
    notification_type: str | None = None,
    sender_id: int | None = None,
    requires_action: bool = False,
):
    notification = model.Notification(
        user_id=user_id,
        item_id=item_id,
        title=title,
        message=message,
        timestamp=datetime.now(),
        is_read=False,
        notification_type=notification_type,
        sender_id=sender_id,
        requires_action=requires_action,
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

    if not notification.requires_action:
        notification.is_read = True
        await db.commit()


    data = {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "timestamp": notification.timestamp,
        "is_read": notification.is_read,
        "item_id": notification.item_id,
        "notification_type": notification.notification_type,
        "sender_id": notification.sender_id,
        "requires_action": notification.requires_action,
        "responded_at": notification.responded_at,
    }

    return data

async def reply_notification(db: AsyncSession, notification_id: int, firebase_uid: str, message: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    result = await db.execute(
        select(model.Notification).where(
            model.Notification.id == notification_id,
            model.Notification.user_id == user.id,
        )
    )
    notification = result.scalars().first()

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not notification.requires_action or notification.responded_at is not None:
        raise HTTPException(status_code=400, detail="This notification cannot be replied")

    if notification.sender_id is None:
        raise HTTPException(status_code=400, detail="Reply target not found")

    await create_notification(
        db=db,
        user_id=notification.sender_id,
        item_id=notification.item_id,
        title="出品者からメッセージが届きました",
        message=message,
        notification_type="seller_reply",
        sender_id=user.id,
        requires_action=False,
    )

    notification.is_read = True
    notification.responded_at = datetime.now()

    await db.commit()

    return {"sent": True}

async def dismiss_notification(db: AsyncSession, notification_id: int, firebase_uid: str):
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
    notification.responded_at = datetime.now()

    await db.commit()

    return {"dismissed": True}