import os
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

from api.routers import browse

app = FastAPI()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

app.include_router(browse.router)

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