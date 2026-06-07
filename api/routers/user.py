from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.schemas.user as user_schema
import api.cruds.user as user_crud

router = APIRouter()

# ユーザー情報を新規登録(サインアップ時)
@router.post("/user", response_model=None)
async def create_user(request: user_schema.NewUser, db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user)):

    firebase_uid = firebase_user["uid"]
    return await user_crud.create_user(db, request, firebase_uid)

# ユーザー情報を取得
@router.get("/user", response_model=user_schema.User)
async def get_user(uid: str, db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user)):

    firebase_uid = firebase_user["uid"]
    return await user_crud.get_user(db, uid)

# ユーザー情報を更新
@router.put("/user", response_model=None)
async def update_user(request: user_schema.UserUpdate, db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user)):

    firebase_uid = firebase_user["uid"]
    return await user_crud.update_user(db, firebase_uid, request)