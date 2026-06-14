from fastapi import HTTPException
from typing import List

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

import api.models as model
import api.schemas.item as item_schema
from api.recommender import calc_recommend_score

async def get_items(db: AsyncSession) -> List[item_schema.ListedItem]:
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
        .where(model.Item.buyer_id.is_(None))
        .order_by(model.Item.posted_at.desc())
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

async def get_item(db: AsyncSession, item_id: int) -> item_schema.ListedItem:

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
        .where(model.Item.id == item_id)
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Item not found")

    row0 = rows[0]

    item = {
        "id": row0["id"],
        "image_url": row0["image_url"],
        "name": row0["name"],
        "description": row0["description"],
        "price": row0["price"],
        "posted_at": row0["posted_at"],
        "seller_id": row0["seller_id"],
        "buyer_id": row0["buyer_id"],
        "c0_id": row0["c0_id"],
        "c1_id": row0["c1_id"],
        "c0_name": row0["c0_name"],
        "c1_name": row0["c1_name"],
        "seller": row0["seller"],
        "tags": [],
    }

    for row in rows:
        if row["tag"] is not None:
            item["tags"].append(row["tag"])

    return item_schema.ListedItem(**item)

async def get_recommended_items(
    db: AsyncSession,
    item_id: int,
    limit: int = 4,
) -> List[item_schema.ListedItem]:
    current_result = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    current_item = current_result.scalars().first()

    if current_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    candidate_result = await db.execute(
        select(model.Item).where(
            model.Item.id != item_id,
            model.Item.buyer_id.is_(None),
        )
    )
    candidate_items = candidate_result.scalars().all()

    scored_items = []

    for candidate_item in candidate_items:
        score = calc_recommend_score(current_item, candidate_item)
        scored_items.append((candidate_item.id, score))

    scored_items.sort(key=lambda pair: pair[1], reverse=True)

    recommended_ids = [item_id for item_id, _ in scored_items[:limit]]

    if not recommended_ids:
        return []

    all_items = await get_items(db)
    item_by_id = {item.id: item for item in all_items}

    return [
        item_by_id[item_id]
        for item_id in recommended_ids
        if item_id in item_by_id
    ]
    