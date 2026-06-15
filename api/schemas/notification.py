from datetime import datetime
from pydantic import BaseModel


class NotificationSummary(BaseModel):
    id: int
    title: str
    timestamp: datetime
    is_read: bool
    item_id: int | None = None

    model_config = {
        "from_attributes": True
    }


class NotificationDetail(BaseModel):
    id: int
    title: str
    message: str
    timestamp: datetime
    is_read: bool
    item_id: int | None = None

    model_config = {
        "from_attributes": True
    }


class UnreadCount(BaseModel):
    unread_count: int