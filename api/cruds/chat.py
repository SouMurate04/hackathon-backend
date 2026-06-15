from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.chat as chat_schema
import api.cruds.notification as notification_crud


async def create_message(
    db: AsyncSession,
    firebase_uid: str,
    request: chat_schema.NewChatMessage,
):
    user_result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    user = user_result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    item_result = await db.execute(
        select(model.Item).where(model.Item.id == request.item_id)
    )
    item = item_result.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    user_id = user.id
    user_name = user.name
    user_icon_url = user.icon_url

    chat = model.Chat(
        item_id=request.item_id,
        user_id=user_id,
        message=request.message.strip(),
        timestamp=datetime.now(),
    )

    participant_result = await db.execute(
        select(model.Chat.user_id).where(model.Chat.item_id == request.item_id)
    )
    participant_user_ids = {row[0] for row in participant_result.all()}

    notification_user_ids = participant_user_ids | {item.seller_id}
    notification_user_ids.discard(user_id)

    for notification_user_id in notification_user_ids:
        await notification_crud.create_notification(
            db=db,
            user_id=notification_user_id,
            item_id=item.id,
            title="チャットに新しいメッセージがあります",
            message=f"「{item.name}」のチャットに新しいメッセージが投稿されました。",
        )

    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    return {
        "id": chat.id,
        "item_id": chat.item_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_icon_url": user_icon_url,
        "message": chat.message,
        "timestamp": chat.timestamp,
    }


async def get_messages(
    db: AsyncSession,
    item_id: int,
):
    item_result = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    item = item_result.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await db.execute(
        select(
            model.Chat.id.label("id"),
            model.Chat.item_id.label("item_id"),
            model.Chat.user_id.label("user_id"),
            model.User.name.label("user_name"),
            model.User.icon_url.label("user_icon_url"),
            model.Chat.message.label("message"),
            model.Chat.timestamp.label("timestamp"),
        )
        .join(model.User, model.Chat.user_id == model.User.id)
        .where(model.Chat.item_id == item_id)
        .order_by(model.Chat.timestamp.asc())
    )

    return result.mappings().all()