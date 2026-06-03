from pydantic import BaseModel, datatime

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