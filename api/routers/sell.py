import json
import os
from uuid import uuid4

from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from google import genai
from google.genai import types
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.schemas.item as item_schema
import api.cruds.sell as sell_crud


router = APIRouter()

# 商品出品
@router.post("/sell", response_model=None)
async def create_item(
    name: str = Form(...), price: int = Form(...),
    description: str = Form(""), image: UploadFile = File(...), 
    c0_id: int = Form(...), c1_id: int = Form(...),
    tags: List[str] = Form([]),
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

    request = item_schema.NewItem(
        name=name,
        price=price,
        description=description,
        image_url=image_url,
        c0_id=c0_id,
        c1_id=c1_id,
        tags=tags)
    firebase_uid = firebase_user["uid"]
    return await sell_crud.create_item(db, firebase_uid, request)

# 出品情報取得
@router.get("/sell/{user_id}", response_model=List[item_schema.ListedItem])
async def list_notifications(user_id: int, db: AsyncSession = Depends(get_db)):
    return await sell_crud.get_CreatedItems(db, user_id)

@router.put("/sell/{item_id}", response_model=None)
async def update_item(
    item_id: int,
    name: str = Form(...),
    price: int = Form(...),
    description: str = Form(""),
    c0_id: int = Form(...),
    c1_id: int = Form(...),
    tags: List[str] = Form([]),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    image_url = None

    if image is not None:
        bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not bucket_name:
            raise HTTPException(status_code=500, detail="GCS bucket is not configured")

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        object_name = f"items/{uuid4()}.{image.filename.split('.')[-1]}"
        blob = bucket.blob(object_name)
        blob.upload_from_file(image.file, content_type=image.content_type)
        image_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"

    firebase_uid = firebase_user["uid"]

    return await sell_crud.update_item(
        db=db,
        item_id=item_id,
        firebase_uid=firebase_uid,
        name=name,
        price=price,
        description=description,
        c0_id=c0_id,
        c1_id=c1_id,
        tags=tags,
        image_url=image_url,
    )


@router.delete("/sell/{item_id}", response_model=None)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await sell_crud.delete_item(db, item_id, firebase_uid)

@router.post("/sell/recommend", response_model=item_schema.GeneratedIntroduction)
async def generate_introduction(
    image: UploadFile = File(...),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Image file is required")

    image_bytes = await image.read()

    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image is too large")

    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION = "us-central1"
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

    prompt = """
            あなたはフリマアプリの出品文作成アシスタントです。
            画像の商品を見て、商品名と紹介文を日本語で作成してください。

            条件:
            - 商品名は短く自然にする
            - 紹介文は80〜150文字程度
            - 画像から分からないブランド名、型番、状態、サイズは断定しない
            - 誇大表現は避ける
            - 必ずJSONのみを返す
            - JSONの形式は {"name": "...", "description": "..."} にする
            """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image.content_type,
                ),
                prompt,
            ],
        )

        text = response.text.strip()

        # 念のため Markdown コードブロックを除去
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        data = json.loads(text)

        return item_schema.GeneratedIntroduction(
            name=data["name"],
            description=data["description"],
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Gemini response was not valid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))