import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel

from api.routers import user

app = FastAPI()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

app.include_router(user.router)
'''
app.include_router(browse.router)
app.include_router(sell.router)
app.include_router(buy.router)
app.include_router(like.router)
app.include_router(chat.router)
app.include_router(notify.router)
'''

app.add_middleware(
    CORSMiddleware,
    allow_origins=["hackathon-frontend-six-phi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello FastAPI"}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_gemini(request: ChatRequest):
    try:
        # Vertex AI経由のGeminiモデルを指定（例: gemini-2.5-flash）
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.message,
        )
        return {"response": response.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))