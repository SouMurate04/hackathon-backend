from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.schemas.item as item_schema
import api.cruds.browse as browse_crud

router = APIRouter()

# 商品一覧を取得
@router.get("/browse", response_model=List[item_schema.ListedItem])
async def list_items(
    keyword: str | None = Query(None),
    c0_id: int | None = Query(None),
    c1_id: int | None = Query(None),
    min_price: int | None = Query(None),
    max_price: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await browse_crud.search_items(
        db=db,
        keyword=keyword,
        c0_id=c0_id,
        c1_id=c1_id,
        min_price=min_price,
        max_price=max_price,
    )

@router.post(
    "/browse/ai-recommendation",
    response_model=item_schema.AIRecommendationResponse,
)
async def ai_recommendation(
    request: item_schema.AIRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    return await browse_crud.get_ai_recommendation(db, request)

@router.get("/browse/popular-tags")
async def get_popular_tags(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    return await browse_crud.get_popular_tags(db, limit)

@router.get("/browse/subscription", response_model=List[item_schema.ListedItem])
async def get_subscription_items(
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await browse_crud.get_subscription_items(db, firebase_user["uid"])

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