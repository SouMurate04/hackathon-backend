from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.schemas.user as user_schema

async def create_user(db: AsyncSession, new_user: user_schema.NewUser, firebase_uid: str):
    record = model.User(
        firebase_uid=firebase_uid,
        name=new_user.name,
        email=new_user.email
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return

async def get_user_me(db: AsyncSession, firebase_uid: str) -> user_schema.User:
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    return result.scalars().first() 

async def get_user(db: AsyncSession, user_id: int) -> user_schema.User:
    result = await db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    return result.scalars().first() 


async def update_user(db: AsyncSession, firebase_uid: str, request: user_schema.UpdatedUser):
    user = await get_user(db, firebase_uid)

    user.name = request.name
    user.email = request.email

    await db.commit()
    await db.refresh(user)
    return user