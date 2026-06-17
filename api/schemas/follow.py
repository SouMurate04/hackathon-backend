from pydantic import BaseModel


class FollowSummary(BaseModel):
    followings_count: int
    followers_count: int


class FollowStatus(BaseModel):
    is_following: bool


class FollowUser(BaseModel):
    id: int
    name: str | None = None
    icon_url: str | None = None
    bio: str | None = None

    model_config = {
        "from_attributes": True
    }