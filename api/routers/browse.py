from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.item as item_schema
import api.cruds.browse as browse_crud

router = APIRouter()

# 商品一覧を取得
@router.get("/browse", response_model=List[item_schema.ListedItem])
async def list_items(db: AsyncSession = Depends(get_db)):
    return await browse_crud.get_items(db)

@router.get("/browse/{item_id}", response_model=item_schema.ListedItem)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    return await browse_crud.get_item(db, item_id)

@router.get(
    "/browse/{item_id}/recommendations",
    response_model=List[item_schema.ListedItem],
)
async def get_recommended_items(
    item_id: int,
    limit: int = 4,
    db: AsyncSession = Depends(get_db),
):
    return await browse_crud.get_recommended_items(db, item_id, limit)