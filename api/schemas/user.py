from pydantic import BaseModel

class NewUser(BaseModel):
    email: str

class UpdatedUser(BaseModel):
    name: str
    email: str
    icon_url: str | None = None
    bio: str | None = None
    delivery_place_type: str | None = None
    postal_code: str | None = None
    address_city: str | None = None
    address_street: str | None = None
    address_building: str | None = None


class User(BaseModel):
    id: int
    firebase_uid: str
    name: str
    email: str
    icon_url: str | None = None
    bio: str | None = None
    delivery_place_type: str | None = None
    postal_code: str | None = None
    address_city: str | None = None
    address_street: str | None = None
    address_building: str | None = None