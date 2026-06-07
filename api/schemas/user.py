from pydantic import BaseModel

class NewUser(BaseModel):
    name: str
    email: str

class UpdateUser(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    firebase_uid: str
    name: str
    email: str

    model_config = {
        "from_attributes": True
    }