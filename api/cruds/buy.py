from typing import List
from datetime import datetime

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
import api.models as model
import api.schemas.item as item_schema
import api.cruds.notification as notification_crud

async def buy_item(db: AsyncSession, item_id: int, firebase_uid: str, request):
    user_ret = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    buyer = user_ret.scalars().first()

    if buyer is None:
        raise HTTPException(status_code=404, detail="User not found")

    item_ret = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    item = item_ret.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if request.delivery_place_type in ["home_handoff", "home_delivery_box"]:
        if not request.postal_code or not request.address_city or not request.address_street:
            raise HTTPException(status_code=400, detail="Shipping address is incomplete")

    if request.delivery_place_type == "pickup_point":
        if not request.address_building:
            raise HTTPException(status_code=400, detail="Pickup point name is required")

    if item.buyer_id is not None:
        raise HTTPException(status_code=400, detail="Item is already sold")

    if request.save_as_default:
        buyer.delivery_place_type = request.delivery_place_type
        buyer.postal_code = request.postal_code
        buyer.address_city = request.address_city
        buyer.address_street = request.address_street
        buyer.address_building = request.address_building

    item.buyer_id = buyer.id
    item.bought_at = datetime.now()

    shipping_text = "\n".join([
        f"配送先種別: {request.delivery_place_type}",
        f"郵便番号: {request.postal_code or ''}",
        f"都道府県・市区町村: {request.address_city or ''}",
        f"町域・番地: {request.address_street or ''}",
        f"建物名・店舗名: {request.address_building or ''}",
    ])

    buyer_message = request.message_to_seller.strip() if request.message_to_seller else ""

    message = f"あなたが出品した「{item.name}」が購入されました。\n\n{shipping_text}"

    if buyer_message:
        message += f"\n\n購入者からのメッセージ:\n{buyer_message}"

    await notification_crud.create_notification(
        db=db,
        user_id=item.seller_id,
        item_id=item.id,
        title="商品が購入されました",
        message=message,
        notification_type="item_purchased",
        sender_id=buyer.id,
        requires_action=True,
    )

    like_result = await db.execute(
        select(model.Like.user_id).where(model.Like.item_id == item.id)
    )
    liked_user_ids = {row[0] for row in like_result.all()}

    for liked_user_id in liked_user_ids:
        if liked_user_id == buyer.id:
            continue
        if liked_user_id == item.seller_id:
            continue

        await notification_crud.create_notification(
            db=db,
            user_id=liked_user_id,
            item_id=item.id,
            title="いいねした商品が購入されました",
            message=f"いいねしていた「{item.name}」が他のユーザーに購入されました。",
        )

    await db.commit()
    await db.refresh(item)
    return

async def get_bought_items(
    db: AsyncSession,
    firebase_uid: str,
) -> List[item_schema.ListedItem]:
    user_result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    buyer = user_result.scalars().first()

    if buyer is None:
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
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
        .where(model.Item.buyer_id == buyer.id)
        .order_by(model.Item.bought_at.desc())
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