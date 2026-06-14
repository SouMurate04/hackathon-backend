from typing import List

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

import api.models as model
import api.schemas.item as item_schema


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

async def get_liked_items(
    db: AsyncSession,
    user_id: int,
) -> List[item_schema.ListedItem]:
    user_result = await db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = user_result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    CategoryC0 = aliased(model.Category)
    CategoryC1 = aliased(model.Category)

    query = (
        select(
            model.Item.id.label("id"),
            model.Item.name.label("name"),
            model.Item.description.label("description"),
            model.Item.price.label("price"),
            model.Item.posted_at.label("posted_at"),
            model.Item.seller_id.label("seller_id"),
            model.Item.buyer_id.label("buyer_id"),
            model.Item.c0_id.label("c0_id"),
            model.Item.c1_id.label("c1_id"),
            CategoryC0.name.label("c0_name"),
            CategoryC1.name.label("c1_name"),
            model.User.name.label("seller"),
            model.Image.url.label("image_url"),
            model.Tag.name.label("tag"),
        )
        .join(model.Like, model.Like.item_id == model.Item.id)
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Like.user_id == user_id)
        .order_by(model.Item.id.desc())
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    items_by_id = {}

    for row in rows:
        item_id = row["id"]

        if item_id not in items_by_id:
            items_by_id[item_id] = {
                "id": row["id"],
                "image_url": row["image_url"],
                "name": row["name"],
                "description": row["description"],
                "price": row["price"],
                "posted_at": row["posted_at"],
                "seller_id": row["seller_id"],
                "buyer_id": row["buyer_id"],
                "c0_id": row["c0_id"],
                "c1_id": row["c1_id"],
                "c0_name": row["c0_name"],
                "c1_name": row["c1_name"],
                "seller": row["seller"],
                "tags": [],
            }

        if row["tag"] is not None:
            items_by_id[item_id]["tags"].append(row["tag"])

    return [item_schema.ListedItem(**item) for item in items_by_id.values()]