from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.category as category_schema


async def get_categories(db: AsyncSession) -> list[category_schema.CategoryTree]:
    result = await db.execute(
        select(model.Category)
        .order_by(model.Category.level, model.Category.parent_id, model.Category.id)
    )

    categories = result.scalars().all()

    parents = {}
    children = []

    for category in categories:
        if category.level == 0:
            parents[category.id] = {
                "id": category.id,
                "name": category.name,
                "children": [],
            }
        elif category.level == 1:
            children.append(category)

    for child in children:
        if child.parent_id in parents:
            parents[child.parent_id]["children"].append({
                "id": child.id,
                "name": child.name,
            })

    return [
        category_schema.CategoryTree(**category)
        for category in parents.values()
    ]