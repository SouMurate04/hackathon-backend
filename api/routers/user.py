from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.user as user_schema
import api.cruds.user as user_crud

router = APIRouter()

# ユーザー情報を新規登録(サインアップ時)
@router.post("/user", response_model=None)
async def create_user(request: user_schema.NewUser, db: AsyncSession = Depends(get_db)):
    return await user_crud.create_user(db, request)

# ユーザー情報を取得
@router.get("/user", response_model=user_schema.User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_user(db, user_id)

# ユーザー情報を更新
@router.put("/user", response_model=user_schema.User)
async def update_user(user: user_schema.User, db: AsyncSession = Depends(get_db)):
    return await crud.update_user(db, user)