from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

router = APIRouter()

# いいねをつける
@router.post("/like", response_model=None)
async def like_item(item_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.like_item(db, user_id, item_id)

# いいねを消す
@router.delete("/like/{like_id}", response_model=None)
async def unlike_item(like_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.unlike_item(db, like_id)