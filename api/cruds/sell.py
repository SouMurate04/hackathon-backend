from fastapi import HTTPException

from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

import api.models as model
import api.schemas.item as item_schema
import api.cruds.notification as notification_crud

async def create_item(db: AsyncSession, firebase_uid: str, new_item: item_schema.NewItem):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    seller = result.scalars().first()

    if seller is None:
        raise ValueError("User not found")
    
    item_record = model.Item(
        name=new_item.name,
        description=new_item.description,
        price=new_item.price,
        c0_id=new_item.c0_id,
        c1_id=new_item.c1_id,
        seller_id=seller.id,
        posted_at=datetime.now()
    )

    db.add(item_record)
    await db.flush()

    follower_result = await db.execute(
        select(model.Follow.follower_id).where(model.Follow.followee_id == seller.id)
    )
    follower_ids = {row[0] for row in follower_result.all()}

    for follower_id in follower_ids:
        await notification_crud.create_notification(
            db=db,
            user_id=follower_id,
            item_id=item_record.id,
            title=f"{seller.name or 'ユーザー'}さんが新たに出品しました",
            message=f"{seller.name or 'ユーザー'}さんが新たに「{item_record.name}」を出品しました。",
            notification_type="followed_seller_item",
            sender_id=seller.id,
        )

    for image_url in new_item.image_urls:
        db.add(model.Image(
            item_id=item_record.id,
            url=image_url,
        ))

    for tag in new_item.tags:
        tag_record = model.Tag(
            item_id=item_record.id,
            name=tag
        )

        db.add(tag_record)

    await db.commit()
    await db.refresh(item_record)
    return

async def get_CreatedItems(db: AsyncSession, user_id: int):
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
        .where(model.Item.seller_id == user_id)
        .join(model.User, model.Item.seller_id == model.User.id)
        .outerjoin(CategoryC0, model.Item.c0_id == CategoryC0.id)
        .outerjoin(CategoryC1, model.Item.c1_id == CategoryC1.id)
        .outerjoin(model.Image, model.Item.id == model.Image.item_id)
        .outerjoin(model.Tag, model.Item.id == model.Tag.item_id)
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

async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    return result.scalars().first()

async def update_item(
    db: AsyncSession,
    item_id: int,
    firebase_uid: str,
    name: str,
    price: int,
    description: str,
    c0_id: int,
    c1_id: int,
    tags: list[str],
    image_urls: list[str] | None,
):
    seller = await get_user_by_firebase_uid(db, firebase_uid)

    if seller is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    item = result.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="You are not the seller")

    if item.buyer_id is not None:
        raise HTTPException(status_code=400, detail="Sold item cannot be edited")

    item.name = name
    item.price = price
    item.description = description
    item.c0_id = c0_id
    item.c1_id = c1_id

    if image_urls is not None:
        await db.execute(
            delete(model.Image).where(model.Image.item_id == item_id)
        )

        for image_url in image_urls:
            db.add(model.Image(item_id=item_id, url=image_url))

    await db.execute(
        delete(model.Tag).where(model.Tag.item_id == item_id)
    )

    for tag in tags:
        if tag:
            db.add(model.Tag(item_id=item_id, name=tag))

    await db.commit()

    return {"updated": True}

async def delete_item(
    db: AsyncSession,
    item_id: int,
    firebase_uid: str,
):
    seller = await get_user_by_firebase_uid(db, firebase_uid)

    if seller is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(model.Item).where(model.Item.id == item_id)
    )
    item = result.scalars().first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="You are not the seller")

    if item.buyer_id is not None:
        raise HTTPException(status_code=400, detail="Sold item cannot be deleted")

    like_result = await db.execute(
        select(model.Like.user_id).where(model.Like.item_id == item.id)
    )
    liked_user_ids = {row[0] for row in like_result.all()}

    for liked_user_id in liked_user_ids:
        if liked_user_id == seller.id:
            continue

        await notification_crud.create_notification(
            db=db,
            user_id=liked_user_id,
            item_id=None,
            title=f"いいねした「{item.name}」の出品が取り下げられました。",
            message=(
                f"あなたがいいねしていた「{item.name}」についてですが、"
                f"{seller.name or '出品者'}さんが出品を取り下げたため購入できなくなりました。"
                "ご了承ください。"
            ),
            notification_type="liked_item_deleted",
            sender_id=seller.id,
        )

    await db.execute(delete(model.Like).where(model.Like.item_id == item_id))
    await db.execute(delete(model.Image).where(model.Image.item_id == item_id))
    await db.execute(delete(model.Tag).where(model.Tag.item_id == item_id))
    await db.execute(delete(model.Chat).where(model.Chat.item_id == item_id))
    await db.execute(delete(model.Notification).where(model.Notification.item_id == item_id))
    await db.execute(delete(model.Item).where(model.Item.id == item_id))

    await db.commit()

    return {"deleted": True}