from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.firebase_auth import get_current_firebase_user

import api.cruds.chat as chat_crud
import api.schemas.chat as chat_schema

router = APIRouter()


@router.get("/chat/{item_id}", response_model=List[chat_schema.ChatMessage])
async def get_messages(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await chat_crud.get_messages(db, item_id)


@router.post("/chat", response_model=chat_schema.ChatMessage)
async def create_message(
    request: chat_schema.NewChatMessage,
    db: AsyncSession = Depends(get_db),
    firebase_user: dict = Depends(get_current_firebase_user),
):
    firebase_uid = firebase_user["uid"]
    return await chat_crud.create_message(db, firebase_uid, request)