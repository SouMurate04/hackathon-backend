from typing import List

from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.ext.asyncio import AsyncSession

import api.models.item as model
import api.schemas.item as item_schema

async def get_items(db: AsyncSession) -> List[item_schema.Item]:
    result: Result = await(
        db.execute(select(model.Item))
    )
    rows = result.all()
    return [item_schema.Item(**row[0]) for row in rows]