from typing import List
from datetime import datetime

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.ext.asyncio import AsyncSession

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