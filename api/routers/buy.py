from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.message as message_schema

router = APIRouter()

# 購入を確定
@router.post("/buy", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 購入情報を取得
@router.get("/buy", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 購入情報を更新
@router.put("/buy", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 購入取り下げ
@router.delete("/buy", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)