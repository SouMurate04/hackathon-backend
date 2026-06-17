from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

import api.models as model
import api.cruds.notification as notification_crud


async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str):
    result = await db.execute(
        select(model.User).where(model.User.firebase_uid == firebase_uid)
    )
    return result.scalars().first()


async def follow_user(db: AsyncSession, followee_id: int, firebase_uid: str):
    follower = await get_user_by_firebase_uid(db, firebase_uid)

    if follower is None:
        raise HTTPException(status_code=404, detail="User not found")

    if follower.id == followee_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    followee_result = await db.execute(
        select(model.User).where(model.User.id == followee_id)
    )
    followee = followee_result.scalars().first()

    if followee is None:
        raise HTTPException(status_code=404, detail="Followee not found")

    existing_result = await db.execute(
        select(model.Follow).where(
            model.Follow.followee_id == followee_id,
            model.Follow.follower_id == follower.id,
        )
    )
    existing_follow = existing_result.scalars().first()

    if existing_follow is not None:
        return {"is_following": True}

    db.add(model.Follow(
        followee_id=followee_id,
        follower_id=follower.id,
    ))

    await notification_crud.create_notification(
        db=db,
        user_id=followee_id,
        item_id=None,
        title="新しいフォロワーがいます",
        message=f"{follower.name or 'ユーザー'}さんにフォローされました。",
    )

    await db.commit()

    return {"is_following": True}


async def unfollow_user(db: AsyncSession, followee_id: int, firebase_uid: str):
    follower = await get_user_by_firebase_uid(db, firebase_uid)

    if follower is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        delete(model.Follow).where(
            model.Follow.followee_id == followee_id,
            model.Follow.follower_id == follower.id,
        )
    )

    await db.commit()

    return {"is_following": False}


async def get_follow_summary(db: AsyncSession, user_id: int):
    followings_result = await db.execute(
        select(func.count(model.Follow.id)).where(
            model.Follow.follower_id == user_id
        )
    )

    followers_result = await db.execute(
        select(func.count(model.Follow.id)).where(
            model.Follow.followee_id == user_id
        )
    )

    return {
        "followings_count": followings_result.scalar_one(),
        "followers_count": followers_result.scalar_one(),
    }


async def get_follow_status(db: AsyncSession, user_id: int, firebase_uid: str):
    current_user = await get_user_by_firebase_uid(db, firebase_uid)

    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(model.Follow).where(
            model.Follow.followee_id == user_id,
            model.Follow.follower_id == current_user.id,
        )
    )

    return {"is_following": result.scalars().first() is not None}


async def get_followings(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(
            model.User.id.label("id"),
            model.User.name.label("name"),
            model.User.icon_url.label("icon_url"),
            model.User.bio.label("bio"),
        )
        .join(model.Follow, model.Follow.followee_id == model.User.id)
        .where(model.Follow.follower_id == user_id)
        .order_by(model.User.id.desc())
    )

    return result.mappings().all()


async def get_followers(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(
            model.User.id.label("id"),
            model.User.name.label("name"),
            model.User.icon_url.label("icon_url"),
            model.User.bio.label("bio"),
        )
        .join(model.Follow, model.Follow.follower_id == model.User.id)
        .where(model.Follow.followee_id == user_id)
        .order_by(model.User.id.desc())
    )

    return result.mappings().all()