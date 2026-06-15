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

from sqlalchemy import select
import api.models as model
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
    db: AsyncSession = Depends(get_db),
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

    prompt = f"""
            あなたはフリマアプリの出品補助AIです。
            画像の商品を見て、商品名、商品紹介文、大カテゴリ、小カテゴリを推測してください。

            カテゴリは必ず以下の一覧から選んでください。
            存在しないカテゴリ名やIDを作ってはいけません。
            小カテゴリは、必ず選んだ大カテゴリのchildrenから選んでください。

            カテゴリ一覧:
            {json.dumps(category_tree, ensure_ascii=False)}

            条件:
            - 商品名は短く自然にする
            - 紹介文は80〜150文字程度
            - 画像から分からないブランド名、型番、状態、サイズは断定しない
            - 誇大表現は避ける
            - 必ずJSONのみを返す
            - JSONの形式は以下にする
            {{
            "name": "...",
            "description": "...",
            "c0_id": 1,
            "c1_id": 10
            }}
            """

    category_result = await db.execute(
        select(model.Category).order_by(model.Category.level, model.Category.id)
    )
    category_rows = category_result.scalars().all()

    c0_categories = [
        category for category in category_rows
        if category.level == 0
    ]

    c1_categories = [
        category for category in category_rows
        if category.level == 1
    ]

    category_tree = []

    for c0 in c0_categories:
        children = [
            {
                "id": c1.id,
                "name": c1.name,
            }
            for c1 in c1_categories
            if c1.parent_id == c0.id
        ]

        category_tree.append({
            "id": c0.id,
            "name": c0.name,
            "children": children,
        })

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image.content_type,
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        data = json.loads(response.text)

        c0_id = data["c0_id"]
        c1_id = data["c1_id"]

        valid_c0_ids = {c0["id"] for c0 in category_tree}
        valid_c1_pairs = {
            (c0["id"], c1["id"])
            for c0 in category_tree
            for c1 in c0["children"]
        }

        if c0_id not in valid_c0_ids:
            raise HTTPException(status_code=500, detail="Gemini returned invalid c0_id")

        if (c0_id, c1_id) not in valid_c1_pairs:
            raise HTTPException(status_code=500, detail="Gemini returned invalid c1_id")

        return item_schema.GeneratedIntroduction(
            name=data["name"],
            description=data["description"],
            c0_id=c0_id,
            c1_id=c1_id,
        )

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