from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.like as like_crud
import api.schemas.item as item_schema

router = APIRouter()


@router.post("/like/{item_id}", response_model=None)
async def like_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await like_crud.like_item(db, item_id, firebase_uid)


@router.delete("/like/{item_id}", response_model=None)
async def unlike_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await like_crud.unlike_item(db, item_id, firebase_uid)


@router.get("/like/{item_id}", response_model=None)
async def is_liked(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await like_crud.is_liked(db, item_id, firebase_uid)

@router.get("/likes/{user_id}", response_model=List[item_schema.ListedItem])
async def get_liked_items(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await like_crud.get_liked_items(db, user_id)