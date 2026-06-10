from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        category_id=new_item.category_id,
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
    query = (select(
        model.Item.id.label("id"),
        model.Item.name.label("name"),
        model.Item.description.label("description"),
        model.Item.price.label("price"),
        model.Item.posted_at.label("posted_at"),
        model.Category.name.label("category"),
        model.User.name.label("seller"),
        model.Image.url.label("image_url"),
        model.Tag.name.label("tag"),
    ).where(model.Item.seller_id == user_id)
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(model.Category, model.Item.category_id == model.Category.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Item.buyer_id.is_(None))
        .order_by(model.Item.posted_at.desc()))

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
                "category": row["category"],
                "seller": row["seller"],
                "tags": [],
            }

        if row["tag"] is not None:
            items_by_id[item_id]["tags"].append(row["tag"])

    return [item_schema.ListedItem(**item) for item in items_by_id.values()]