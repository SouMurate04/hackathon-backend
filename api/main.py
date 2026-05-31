import os
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

app = FastAPI()

# 💡 Google CloudのプロジェクトIDを設定（環境変数から読み込むのがベスト）
# ローカルテスト用なら直接文字列で入れても安全です（APIキーではないため）
PROJECT_ID = os.environ.get("hackathon", "project-49c9d3ce-3959-4f5d-9d5")
LOCATION = "us-central1"  # Geminiが利用可能なリージョンを指定

# Clientを初期化（引数でvertexai=Trueにすると、自動的にADCの認証情報を探しに行きます）
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
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