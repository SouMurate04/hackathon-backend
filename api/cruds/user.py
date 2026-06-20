import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import select, delete, or_

import api.models as model
import api.schemas.user as user_schema

async def create_user(db: AsyncSession, new_user: user_schema.NewUser, firebase_uid: str):
    record = model.User(
        firebase_uid=firebase_uid,
        name="ユーザー",
        email=new_user.email,
        icon_url=os.getenv("DEFAULT_ICON_URL"),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return

async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> user_schema.User:
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    return result.scalars().first() 

async def get_user_by_id(db: AsyncSession, user_id: int) -> user_schema.User:
    result = await db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    return result.scalars().first() 


async def update_user(db: AsyncSession, firebase_uid: str, request: user_schema.UpdatedUser):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    user.name = request.name
    user.email = request.email
    user.icon_url = request.icon_url
    user.bio = request.bio
    user.delivery_place_type = request.delivery_place_type
    user.postal_code = request.postal_code
    user.address_city = request.address_city
    user.address_street = request.address_street
    user.address_building = request.address_building

    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, firebase_uid: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id

    # 1. 削除ユーザーが出品した商品だけ取得
    seller_item_result = await db.execute(
        select(model.Item.id).where(model.Item.seller_id == user_id)
    )
    seller_item_ids = [row[0] for row in seller_item_result.all()]

    # 2. 削除ユーザーが出品した商品に紐づくデータを削除
    if seller_item_ids:
        await db.execute(delete(model.Like).where(model.Like.item_id.in_(seller_item_ids)))
        await db.execute(delete(model.Image).where(model.Image.item_id.in_(seller_item_ids)))
        await db.execute(delete(model.Tag).where(model.Tag.item_id.in_(seller_item_ids)))
        await db.execute(delete(model.Chat).where(model.Chat.item_id.in_(seller_item_ids)))
        await db.execute(delete(model.Notification).where(model.Notification.item_id.in_(seller_item_ids)))
        await db.execute(delete(model.Item).where(model.Item.id.in_(seller_item_ids)))

    # 3. 削除ユーザーが購入しただけの商品は残し、購入者情報だけ外す
    bought_item_result = await db.execute(
        select(model.Item).where(model.Item.buyer_id == user_id)
    )
    bought_items = bought_item_result.scalars().all()

    for item in bought_items:
        item.buyer_id = None
        item.bought_at = None

    # 4. 削除ユーザー自身に紐づく行を削除
    await db.execute(delete(model.Like).where(model.Like.user_id == user_id))
    await db.execute(delete(model.Chat).where(model.Chat.user_id == user_id))

    await db.execute(
        delete(model.Notification).where(
            or_(
                model.Notification.user_id == user_id,
                model.Notification.sender_id == user_id,
            )
        )
    )

    await db.execute(
        delete(model.Follow).where(
            or_(
                model.Follow.followee_id == user_id,
                model.Follow.follower_id == user_id,
            )
        )
    )

    # 5. 最後にユーザーを削除
    await db.execute(delete(model.User).where(model.User.id == user_id))

    await db.commit()

    return {"deleted": True}