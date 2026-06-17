from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.follow as follow_crud
import api.schemas.follow as follow_schema

router = APIRouter()


@router.post("/follow/{followee_id}", response_model=follow_schema.FollowStatus)
async def follow_user(
    followee_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await follow_crud.follow_user(db, followee_id, firebase_user["uid"])


@router.delete("/follow/{followee_id}", response_model=follow_schema.FollowStatus)
async def unfollow_user(
    followee_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await follow_crud.unfollow_user(db, followee_id, firebase_user["uid"])


@router.get("/follow/{user_id}/summary", response_model=follow_schema.FollowSummary)
async def get_follow_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await follow_crud.get_follow_summary(db, user_id)


@router.get("/follow/{user_id}/status", response_model=follow_schema.FollowStatus)
async def get_follow_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    return await follow_crud.get_follow_status(db, user_id, firebase_user["uid"])


@router.get("/follow/{user_id}/followings", response_model=List[follow_schema.FollowUser])
async def get_followings(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await follow_crud.get_followings(db, user_id)


@router.get("/follow/{user_id}/followers", response_model=List[follow_schema.FollowUser])
async def get_followers(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await follow_crud.get_followers(db, user_id)