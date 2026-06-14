from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.like as like_crud

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