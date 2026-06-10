from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.buy as buy_crud

router = APIRouter()

# 購入を確定
@router.post("/buy/{item_id}", response_model=None)
async def buy_item(item_id: int, db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user)):

    firebase_uid = firebase_user["uid"]
    return await buy_crud.buy_item(db, item_id, firebase_uid)

'''
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
'''