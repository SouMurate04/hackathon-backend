import os
from uuid import uuid4

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user
from google.cloud import storage

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
@router.get("/user/me", response_model=user_schema.User)
async def get_user_me(db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user)):

    firebase_uid = firebase_user["uid"]
    return await user_crud.get_user_by_firebase_uid(db, firebase_uid)

@router.get("/user/{user_id}", response_model=user_schema.User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await user_crud.get_user_by_id(db, user_id)

# ユーザー情報を更新
@router.put("/user", response_model=user_schema.User)
async def update_user(
    name: str = Form(...), email: str = Form(...),
    bio: str = Form(""), 
    icon: UploadFile | None = File(None), 
    icon_url: str | None = Form(None),
    delivery_place_type: str | None = Form(None),
    postal_code: str | None = Form(None),
    address_city: str | None = Form(None),
    address_street: str | None = Form(None),
    address_building: str | None = Form(None),
    db: AsyncSession = Depends(get_db), firebase_user: dict = Depends(get_current_firebase_user)
    ):

    if icon is not None:
        bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket is not configured")

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        object_name = f"users/{uuid4()}.{icon.filename.split('.')[-1]}"
        blob = bucket.blob(object_name)
        blob.upload_from_file(icon.file, content_type=icon.content_type)
        final_icon_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"
    else:
        final_icon_url = icon_url

    request = user_schema.UpdatedUser(name=name, email=email, bio=bio, icon_url=final_icon_url,
        delivery_place_type=delivery_place_type, postal_code=postal_code,
        address_city=address_city, address_street=address_street, address_building=address_building)

    firebase_uid = firebase_user["uid"]
    return await user_crud.update_user(db, firebase_uid, request)

# ユーザー削除
@router.delete("/user", response_model=None)
async def delete_user(
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await user_crud.delete_user(db, firebase_uid)