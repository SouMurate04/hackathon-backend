from pydantic import BaseModel, datatime

# 新規商品
class NewItem(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    category_id: int
    tags: list[str] = []

class PostedItem(BaseModel):
    name: str
    description: str
    price: int
    category_id: int
    seller_id: int
    posted_at: datetime

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
    catrgory: name
    tags: list[str] = []

    model_config = {
        "from_attributes": True
    }