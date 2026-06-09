from typing import List

from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.item as item_schema

async def get_items(db: AsyncSession) -> List[item_schema.ListedItem]:
    query = select(
        model.Item.id.label["id"],
        model.Item.name.label["name"],
        model.Item.description.label["description"],
        model.Item.price.label["price"],
        model.Item.posted_at.label["posted_at"],
        model.Category.name.label["category"],
        model.User.name.label["seller"],
        model.Image.url.label["image_url"],
        model.Tag.name.label["tag"],
    ).join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(model.Category, model.Item.category_id == model.Category.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .order_by(model.Item.posted_at.desc())

    result = await db.execute(query)
    rows = result.mappings().all()

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
    