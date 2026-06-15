from datetime import datetime
from pydantic import BaseModel


class NewChatMessage(BaseModel):
    item_id: int
    message: str


class ChatMessage(BaseModel):
    id: int
    item_id: int
    user_id: int
    user_name: str | None = None
    user_icon_url: str | None = None
    message: str
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }