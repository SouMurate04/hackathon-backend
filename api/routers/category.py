from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db

import api.schemas.category as category_schema
import api.cruds.category as category_crud

router = APIRouter()

@router.get("/categories", response_model=list[category_schema.CategoryTree])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await category_crud.get_categories(db)