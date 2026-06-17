import json
import os
from google import genai
from google.genai import types

from fastapi import HTTPException
from typing import List

from sqlalchemy import select, func
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

import api.models as model
import api.schemas.item as item_schema
from api.recommender import calc_recommend_score

def parse_search_words(keyword: str) -> tuple[list[str], list[str]]:
    normal_keywords = []
    tag_keywords = []

    for word in keyword.split(" "):
        word = word.strip()
        if not word:
            continue

        if word.startswith("#") and len(word) > 1:
            tag_keywords.append(word[1:].lower())
        else:
            normal_keywords.append(word.lower())

    return normal_keywords, tag_keywords

async def get_items(db: AsyncSession) -> List[item_schema.ListedItem]:
    CategoryC0 = aliased(model.Category)
    CategoryC1 = aliased(model.Category)

    query = (
        select(
            model.Item.id.label("id"),
            model.Item.name.label("name"),
            model.Item.description.label("description"),
            model.Item.price.label("price"),
            model.Item.posted_at.label("posted_at"),
            model.Item.seller_id.label("seller_id"),
            model.Item.buyer_id.label("buyer_id"),
            model.Item.c0_id.label("c0_id"),
            model.Item.c1_id.label("c1_id"),
            CategoryC0.name.label("c0_name"),
            CategoryC1.name.label("c1_name"),
            model.User.name.label("seller"),
            model.Image.url.label("image_url"),
            model.Tag.name.label("tag"),
        )
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Item.buyer_id.is_(None))
        .order_by(model.Item.posted_at.desc())
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    items_by_id = {}

    for row in rows:
        item_id = row["id"]

        if item_id not in items_by_id:
            items_by_id[item_id] = {
                "id": row["id"],
                "image_url": row["image_url"],
                "name": row["name"],
                "description": row["description"],
                "price": row["price"],
                "posted_at": row["posted_at"],
                "seller_id": row["seller_id"],
                "buyer_id": row["buyer_id"],
                "c0_id": row["c0_id"],
                "c1_id": row["c1_id"],
                "c0_name": row["c0_name"],
                "c1_name": row["c1_name"],
                "seller": row["seller"],
                "tags": [],
            }

        if row["tag"] is not None:
            items_by_id[item_id]["tags"].append(row["tag"])

    return [item_schema.ListedItem(**item) for item in items_by_id.values()]

async def get_item(db: AsyncSession, item_id: int) -> item_schema.ListedItem:

    CategoryC0 = aliased(model.Category)
    CategoryC1 = aliased(model.Category)

    query = (
        select(
            model.Item.id.label("id"),
            model.Item.name.label("name"),
            model.Item.description.label("description"),
            model.Item.price.label("price"),
            model.Item.posted_at.label("posted_at"),
            model.Item.seller_id.label("seller_id"),
            model.Item.buyer_id.label("buyer_id"),
            model.Item.c0_id.label("c0_id"),
            model.Item.c1_id.label("c1_id"),
            CategoryC0.name.label("c0_name"),
            CategoryC1.name.label("c1_name"),
            model.User.name.label("seller"),
            model.Image.url.label("image_url"),
            model.Tag.name.label("tag"),
        )
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Item.id == item_id)
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Item not found")

    row0 = rows[0]

    item = {
        "id": row0["id"],
        "image_url": row0["image_url"],
        "name": row0["name"],
        "description": row0["description"],
        "price": row0["price"],
        "posted_at": row0["posted_at"],
        "seller_id": row0["seller_id"],
        "buyer_id": row0["buyer_id"],
        "c0_id": row0["c0_id"],
        "c1_id": row0["c1_id"],
        "c0_name": row0["c0_name"],
        "c1_name": row0["c1_name"],
        "seller": row0["seller"],
        "tags": [],
    }

    for row in rows:
        if row["tag"] is not None:
            item["tags"].append(row["tag"])

    return item_schema.ListedItem(**item)

async def get_recommended_items(
    db: AsyncSession,
    item_id: int,
    limit: int = 4,
) -> List[item_schema.ListedItem]:
    current_result = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    current_item = current_result.scalars().first()

    if current_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    candidate_result = await db.execute(
        select(model.Item).where(
            model.Item.id != item_id,
            model.Item.buyer_id.is_(None),
        )
    )
    candidate_items = candidate_result.scalars().all()

    scored_items = []

    for candidate_item in candidate_items:
        score = calc_recommend_score(current_item, candidate_item)
        scored_items.append((candidate_item.id, score))

    scored_items.sort(key=lambda pair: pair[1], reverse=True)

    recommended_ids = [item_id for item_id, _ in scored_items[:limit]]

    if not recommended_ids:
        return []

    all_items = await get_items(db)
    item_by_id = {item.id: item for item in all_items}

    return [
        item_by_id[item_id]
        for item_id in recommended_ids
        if item_id in item_by_id
    ]

async def get_subscription_items(
    db: AsyncSession,
    firebase_uid: str,
) -> List[item_schema.ListedItem]:
    user_result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    current_user = user_result.scalars().first()

    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    CategoryC0 = aliased(model.Category)
    CategoryC1 = aliased(model.Category)

    query = (
        select(
            model.Item.id.label("id"),
            model.Item.name.label("name"),
            model.Item.description.label("description"),
            model.Item.price.label("price"),
            model.Item.posted_at.label("posted_at"),
            model.Item.seller_id.label("seller_id"),
            model.Item.buyer_id.label("buyer_id"),
            model.Item.c0_id.label("c0_id"),
            model.Item.c1_id.label("c1_id"),
            CategoryC0.name.label("c0_name"),
            CategoryC1.name.label("c1_name"),
            model.User.name.label("seller"),
            model.Image.url.label("image_url"),
            model.Tag.name.label("tag"),
        )
        .join(model.Follow, model.Follow.followee_id == model.Item.seller_id)
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Follow.follower_id == current_user.id)
        .where(model.Item.buyer_id.is_(None))
        .order_by(model.Item.posted_at.desc())
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    items_by_id = {}

    for row in rows:
        item_id = row["id"]

        if item_id not in items_by_id:
            items_by_id[item_id] = {
                "id": row["id"],
                "image_url": row["image_url"],
                "name": row["name"],
                "description": row["description"],
                "price": row["price"],
                "posted_at": row["posted_at"],
                "seller_id": row["seller_id"],
                "buyer_id": row["buyer_id"],
                "c0_id": row["c0_id"],
                "c1_id": row["c1_id"],
                "c0_name": row["c0_name"],
                "c1_name": row["c1_name"],
                "seller": row["seller"],
                "tags": [],
            }

        if row["tag"] is not None:
            items_by_id[item_id]["tags"].append(row["tag"])

    return [item_schema.ListedItem(**item) for item in items_by_id.values()]

async def search_items(
    db: AsyncSession,
    keyword: str | None = None,
    c0_id: int | None = None,
    c1_id: int | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
) -> List[item_schema.ListedItem]:
    normal_keywords, tag_keywords = parse_search_words(keyword or "")

    has_filter = (
        c0_id is not None
        or c1_id is not None
        or min_price is not None
        or max_price is not None
    )

    if not normal_keywords and not tag_keywords and not has_filter:
        return await get_items(db)

    CategoryC0 = aliased(model.Category)
    CategoryC1 = aliased(model.Category)

    query = (
        select(
            model.Item.id.label("id"),
            model.Item.name.label("name"),
            model.Item.description.label("description"),
            model.Item.price.label("price"),
            model.Item.posted_at.label("posted_at"),
            model.Item.seller_id.label("seller_id"),
            model.Item.buyer_id.label("buyer_id"),
            model.Item.c0_id.label("c0_id"),
            model.Item.c1_id.label("c1_id"),
            CategoryC0.name.label("c0_name"),
            CategoryC1.name.label("c1_name"),
            model.User.name.label("seller"),
            model.Image.url.label("image_url"),
            model.Tag.name.label("tag"),
        )
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Item.buyer_id.is_(None))
    )

    if c0_id is not None:
        query = query.where(model.Item.c0_id == c0_id)

    if c1_id is not None:
        query = query.where(model.Item.c1_id == c1_id)

    if min_price is not None:
        query = query.where(model.Item.price >= min_price)

    if max_price is not None:
        query = query.where(model.Item.price <= max_price)

    query = query.order_by(model.Item.posted_at.desc())

    result = await db.execute(query)
    rows = result.mappings().all()

    items_by_id = {}

    for row in rows:
        item_id = row["id"]

        if item_id not in items_by_id:
            items_by_id[item_id] = {
                "id": row["id"],
                "image_url": row["image_url"],
                "name": row["name"],
                "description": row["description"],
                "price": row["price"],
                "posted_at": row["posted_at"],
                "seller_id": row["seller_id"],
                "buyer_id": row["buyer_id"],
                "c0_id": row["c0_id"],
                "c1_id": row["c1_id"],
                "c0_name": row["c0_name"],
                "c1_name": row["c1_name"],
                "seller": row["seller"],
                "tags": [],
            }

        if row["tag"] is not None:
            items_by_id[item_id]["tags"].append(row["tag"])

    matched_items = []

    for item in items_by_id.values():
        item_tags = [tag.lower() for tag in item["tags"]]

        searchable_text = " ".join([
            item["name"] or "",
            item["description"] or "",
            item["c0_name"] or "",
            item["c1_name"] or "",
            " ".join(item["tags"]),
        ]).lower()

        matches_normal_keywords = all(
            word in searchable_text
            for word in normal_keywords
        )

        matches_tag_keywords = all(
            tag in item_tags
            for tag in tag_keywords
        )

        if matches_normal_keywords and matches_tag_keywords:
            matched_items.append(item_schema.ListedItem(**item))

    return matched_items
    
async def get_popular_tags(
    db: AsyncSession,
    limit: int = 10,
):
    result = await db.execute(
        select(
            model.Tag.name.label("name"),
            func.count(model.Tag.id).label("count"),
        )
        .join(model.Item, model.Tag.item_id == model.Item.id)
        .where(model.Item.buyer_id.is_(None))
        .group_by(model.Tag.name)
        .order_by(func.count(model.Tag.id).desc())
        .limit(limit)
    )

    return result.mappings().all()

async def get_ai_recommendation(
    db: AsyncSession,
    request: item_schema.AIRecommendationRequest,
) -> item_schema.AIRecommendationResponse:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty")

    if request.use_filter:
        candidates = await search_items(
            db=db,
            keyword=request.keyword,
            c0_id=request.c0_id,
            c1_id=request.c1_id,
            min_price=request.min_price,
            max_price=request.max_price,
        )
    else:
        candidates = await get_items(db)

    if not candidates:
        return item_schema.AIRecommendationResponse(
            answer="条件に合う商品が見つかりませんでした。",
            items=[],
            reasons={},
        )

    # Geminiに渡しすぎないように制限
    candidates = candidates[:50]

    candidate_payload = [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "category": f"{item.c0_name or ''} / {item.c1_name or ''}",
            "tags": item.tags,
        }
        for item in candidates
    ]

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location="us-central1",
    )

    prompt = f"""
あなたはフリマアプリの商品推薦アシスタントです。
ユーザーの質問に対して、候補商品の中からおすすめ商品を少なくとも1つ、最大3つ選んでください。

条件:
- 必ず候補商品のidから選ぶ
- 存在しないidを作らない
- ユーザーの質問に合う理由を日本語で簡潔に説明する
- 回答はJSONのみ
- 商品が複数ある場合は、より質問に合う順に並べる

ユーザーの質問:
{request.question}

候補商品:
{json.dumps(candidate_payload, ensure_ascii=False)}

JSON形式:
{{
  "answer": "全体としての短い回答文",
  "recommendations": [
    {{
      "item_id": 1,
      "reason": "おすすめ理由"
    }}
  ]
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        data = json.loads(response.text)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Gemini response was not valid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    candidate_by_id = {item.id: item for item in candidates}

    selected_items = []
    reasons = {}

    for rec in data.get("recommendations", []):
        item_id = rec.get("item_id")
        reason = rec.get("reason", "")

        if item_id in candidate_by_id and item_id not in reasons:
            selected_items.append(candidate_by_id[item_id])
            reasons[item_id] = reason

        if len(selected_items) >= 3:
            break

    if not selected_items:
        selected_items = candidates[:1]
        reasons[selected_items[0].id] = "条件に近い商品としておすすめします。"

    return item_schema.AIRecommendationResponse(
        answer=data.get("answer", "おすすめ商品を選びました。"),
        items=selected_items,
        reasons=reasons,
    )