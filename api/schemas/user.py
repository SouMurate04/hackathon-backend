from pydantic import BaseModel
from datetime import datetime

class NewUser(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }