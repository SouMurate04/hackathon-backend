from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.message as message_schema

router = APIRouter()

# 出品紹介の生成
@router.post("/sell/intro", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 商品出品
@router.post("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 出品情報取得
@router.get("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 出品情報の更新
@router.put("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 出品取り下げ
@router.delete("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)