from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.item as schema

router = APIRouter()

# 商品一覧を取得
@router.get("/browse", response_model=List[schema.Item])
async def list_items(db: AsyncSession = Depends(get_db)):
    return await crud.get_items_list(db)

# レコメンド商品を取得
@router.get("/browse/recommend", response_model=List[schema.Item])
async def list_recommended_items(db: AsyncSession = Depends(get_db)):
    return await crud.get_recommended_items_list(db)

# 個別ページを取得
@router.get("/browse/item", response_model=schema.Item)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_item(db, item_id)