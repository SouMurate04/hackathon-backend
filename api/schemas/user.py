from pydantic import BaseModel

class NewUser(BaseModel):
    email: str

class UpdatedUser(BaseModel):
    name: str
    email: str
    icon_url: str
    bio: str


class User(BaseModel):
    id: int
    firebase_uid: str
    name: str
    email: str
    icon_url: str | None = None
    bio: str | None = None

    model_config = {
        "from_attributes": True
    }