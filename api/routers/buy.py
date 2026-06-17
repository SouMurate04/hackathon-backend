from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.buy as buy_crud
import api.schemas.item as item_schema
import api.schemas.buy as buy_schema

router = APIRouter()

# 購入を確定
@router.post("/buy/{item_id}", response_model=None)
async def buy_item(
    item_id: int,
    request: buy_schema.BuyRequest,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await buy_crud.buy_item(db, item_id, firebase_uid, request)

@router.get("/buy/me", response_model=List[item_schema.ListedItem])
async def get_my_bought_items(
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),):

    firebase_uid = firebase_user["uid"]
    return await buy_crud.get_bought_items(db, firebase_uid)