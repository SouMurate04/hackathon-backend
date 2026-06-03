from pydantic import BaseModel, datatime

# 各チャット(返り値)
class Chat(Basemodel):
    user_name: str
    message: str
    posted_at: datetime

    model_config = {
        "from_attributes": True
    }