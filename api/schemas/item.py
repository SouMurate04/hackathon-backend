from pydantic import BaseModel
from datetime import datetime

# 新規商品
class NewItem(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    category_id: int
    tags: list[str] = []

class ListedItem(BaseModel):
    id: int
    name: str
    description: str
    price: int
    image_url: str
    category: str
    seller: str
    posted_at: datetime
    tags: list[str] = []

    model_config = {
        "from_attributes": True


# 商品(返り値)
class Item(BaseModel):
    name: str
    description: str
    price: int
    seller: str
    buyer: str | None = None
    posted_at: datetime
    catrgory_id: int
    tags: list[str] = []

    model_config = {
        "from_attributes": True
    }