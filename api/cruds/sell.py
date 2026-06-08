from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.item as item_schema

async def create_item(db: AsyncSession, new_item: item_schema.NewItem, firebase_uid: str):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    seller = result.scalars().first()

    if seller is None:
        raise ValueError("User not found")
    
    record = model.PostedItem(
        name=new_item.name,
        description=new_item.description,
        price=new_item.price,
        category_id=new_item.category_id,
        seller_id=seller.id,
        posted_at=datetime.now()
    )

    db.add(item)
    db.flush()

    record = model.Image(
        item_id=item.id,
        url=new_item.image_url
    )

    db.add(record)
    db.flush()

    for tag in new_item.tags:
        record = model.Tag(
            item_id=item.id,
            name=tag
        )

        db.add(record)
        db.flush()

    await db.commit()
    await db.refresh(item)
    return