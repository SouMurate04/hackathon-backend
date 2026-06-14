from pydantic import BaseModel
from datetime import datetime

# 新規商品
class NewItem(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    c0_id: int
    c1_id: int
    tags: list[str] = []

class ListedItem(BaseModel):
    id: int
    name: str
    description: str
    price: int
    image_url: str
    c0_id: int | None = None
    c1_id: int | None = None
    c0_name: str | None = None
    c1_name: str | None = None
    seller: str
    posted_at: datetime
    buyer_id: int | None = None
    tags: list[str] = []

    model_config = {
        "from_attributes": True
    }


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