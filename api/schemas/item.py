from pydantic import BaseModel
from datetime import datetime

# 新規商品
class NewItem(BaseModel):
    name: str
    description: str
    price: int
    image_urls: list[str]
    c0_id: int
    c1_id: int
    tags: list[str] = []


class ListedItem(BaseModel):
    id: int
    name: str
    description: str
    price: int
    image_url: str | None = None
    image_urls: list[str] = []
    c0_id: int | None = None
    c1_id: int | None = None
    c0_name: str | None = None
    c1_name: str | None = None
    seller_id: int
    seller: str
    posted_at: datetime
    buyer_id: int | None = None
    tags: list[str] = []


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

class GeneratedIntroduction(BaseModel):
    name: str
    description: str
    c0_id: int
    c1_id: int

class AIRecommendationRequest(BaseModel):
    question: str
    use_filter: bool = False
    keyword: str | None = None
    c0_id: int | None = None
    c1_id: int | None = None
    min_price: int | None = None
    max_price: int | None = None


class AIRecommendedItem(BaseModel):
    item_id: int
    reason: str


class AIRecommendationResponse(BaseModel):
    answer: str
    items: list[ListedItem]
    reasons: dict[int, str]