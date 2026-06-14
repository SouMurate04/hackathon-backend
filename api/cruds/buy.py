from typing import List
from datetime import datetime

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
import api.models as model
import api.schemas.item as item_schema

async def buy_item(db: AsyncSession, item_id: int, firebase_uid: str):
    user_ret = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    buyer = user_ret.scalars().first()

    item_ret = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    item = item_ret.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.buyer_id is not None:
        raise HTTPException(status_code=400, detail="Item is already sold")

    item.buyer_id = buyer.id
    item.bought_at = datetime.now()

    await db.commit()
    await db.refresh(item)
    return

async def get_bought_items(
    db: AsyncSession,
    firebase_uid: str,
) -> List[item_schema.ListedItem]:
    user_result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    buyer = user_result.scalars().first()

    if buyer is None:
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
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Item.buyer_id == buyer.id)
        .order_by(model.Item.bought_at.desc())
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