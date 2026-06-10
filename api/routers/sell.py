import os
from uuid import uuid4

from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.schemas.item as item_schema
import api.cruds.sell as sell_crud


router = APIRouter()

# 出品紹介の生成
'''
@router.post("/sell/introduction", response_model=item_schema.GeneratedIntroduction)
async def generate_introduction(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)
'''

# 商品出品
@router.post("/sell", response_model=None)
async def create_item(
    name: str = Form(...), price: int = Form(...),
    description: str = Form(""), image: UploadFile = File(...), 
    category_id: int = Form(...), tags: List[str] = Form([]),
    db: AsyncSession = Depends(get_db), firebase_user: dict = Depends(get_current_firebase_user)
    ):

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS bucket is not configured")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    object_name = f"items/{uuid4()}.{image.filename.split('.')[-1]}"
    blob = bucket.blob(object_name)
    blob.upload_from_file(image.file, content_type=image.content_type)
    image_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"

    request = item_schema.NewItem(name=name, price=price, description=description, image_url=image_url, category_id=category_id, tags=tags)
    firebase_uid = firebase_user["uid"]
    return await sell_crud.create_item(db, firebase_uid, request)

# 出品情報取得
@router.get("/sell/{user_id}", response_model=List[item_schema.ListedItem])
async def list_notifications(user_id: int db: AsyncSession = Depends(get_db)):
    return await sell_crud.get_CreatedItems(db, user_id)

'''
# 出品情報取得
@router.get("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 出品情報の更新
@router.put("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)

# 出品取り下げ
@router.delete("/sell", response_model=message_schema.notification)
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await crud.get_notifications(db)
'''