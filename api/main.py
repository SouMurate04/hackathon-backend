import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.routers import user, sell, browse, buy, category, like, chat, notification

app = FastAPI()

app.include_router(user.router)
app.include_router(sell.router)
app.include_router(browse.router)
app.include_router(buy.router)
app.include_router(category.router)
app.include_router(like.router)
app.include_router(chat.router)
app.include_router(notification.router)

WEB_URL = os.getenv("WEB_URL")
allow_origins = [
    origin
    for origin in [
        WEB_URL,
        "http://localhost:3000",
    ]
    if origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)