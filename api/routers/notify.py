from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.message as message_schema

router = APIRouter()

# 通知を取得
@router.get("/notify", response_model=List[message_schema.notification])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 既読をつける
@router.put("/notify/{notification_id}", response_model=None)
async def read_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.read_notification(db, notification_id)