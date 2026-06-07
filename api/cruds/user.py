from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.user as user_schema

async def create_user(db: AsyncSession, new_user: user_schema.NewUser):
    record = model.User(**new_user.dict())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return