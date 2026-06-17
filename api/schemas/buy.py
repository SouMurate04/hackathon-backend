from pydantic import BaseModel

class BuyRequest(BaseModel):
    delivery_place_type: str
    postal_code: str | None = None
    address_city: str | None = None
    address_street: str | None = None
    address_building: str | None = None
    save_as_default: bool = False
    message_to_seller: str | None = None