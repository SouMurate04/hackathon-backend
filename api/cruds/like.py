from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model


async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    return result.scalars().first()


async def like_item(db: AsyncSession, item_id: int, firebase_uid: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    item_result = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    item = item_result.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    existing_result = await db.execute(
        select(model.Like).where(
            model.Like.item_id == item_id,
            model.Like.user_id == user.id,
        )
    )
    existing_like = existing_result.scalars().first()

    if existing_like is not None:
        return {"liked": True}

    like = model.Like(
        item_id=item_id,
        user_id=user.id,
    )

    db.add(like)
    await db.commit()

    return {"liked": True}


async def unlike_item(db: AsyncSession, item_id: int, firebase_uid: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        delete(model.Like).where(
            model.Like.item_id == item_id,
            model.Like.user_id == user.id,
        )
    )
    await db.commit()

    return {"liked": False}


async def is_liked(db: AsyncSession, item_id: int, firebase_uid: str):
    user = await get_user_by_firebase_uid(db, firebase_uid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(model.Like).where(
            model.Like.item_id == item_id,
            model.Like.user_id == user.id,
        )
    )

    return {"liked": result.scalars().first() is not None}