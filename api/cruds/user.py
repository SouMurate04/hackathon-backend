from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.user as user_schema

async def create_user(db: AsyncSession, email: user_schema.Email):
    record = model.User(**email.dict())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return