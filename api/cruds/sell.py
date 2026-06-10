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
    result = await db.execute(
        select(model.Item).where(model.Item.seller_id == user_id)
    )
    return result.scalars().all()