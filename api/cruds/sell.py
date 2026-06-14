from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

import api.models as model
import api.schemas.item as item_schema

async def create_item(db: AsyncSession, firebase_uid: str, new_item: item_schema.NewItem):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    seller = result.scalars().first()

    if seller is None:
        raise ValueError("User not found")
    
    item_record = model.Item(
        name=new_item.name,
        description=new_item.description,
        price=new_item.price,
        c0_id=new_item.c0_id,
        c1_id=new_item.c1_id,
        seller_id=seller.id,
        posted_at=datetime.now()
    )

    db.add(item_record)
    await db.flush()

    image_record = model.Image(
        item_id=item_record.id,
        url=new_item.image_url
    )

    db.add(image_record)

    for tag in new_item.tags:
        tag_record = model.Tag(
            item_id=item_record.id,
            name=tag
        )

        db.add(tag_record)

    await db.commit()
    await db.refresh(item_record)
    return

async def get_CreatedItems(db: AsyncSession, user_id: int):
    CategoryC0 = aliased(model.Category)
    CategoryC1 = aliased(model.Category)

    query = (
        select(
            model.Item.id.label("id"),
            model.Item.name.label("name"),
            model.Item.description.label("description"),
            model.Item.price.label("price"),
            model.Item.posted_at.label("posted_at"),
            model.Item.buyer_id.label("buyer_id"),
            model.Item.c0_id.label("c0_id"),
            model.Item.c1_id.label("c1_id"),
            CategoryC0.name.label("c0_name"),
            CategoryC1.name.label("c1_name"),
            model.User.name.label("seller"),
            model.Image.url.label("image_url"),
            model.Tag.name.label("tag"),
        )
        .where(model.Item.seller_id == user_id)
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
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