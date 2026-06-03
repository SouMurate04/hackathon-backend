from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.chat as chat_schema

router = APIRouter()

# チャットを投稿
@router.post("/chat", response_model=List[chat_schema.chat])
async def like_item(item_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.like_item(db, user_id, item_id)

# チャットを取得
@router.get("/chat", response_model=List[chat_schema.chat])
async def list_history(item_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_history(db, item_id)

# チャットを削除
@router.delete("/chat/{like_id}", response_model=None)
async def unlike_item(chat_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.unlike_item(db, chat_id)