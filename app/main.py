import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from app.services.uroboros_engine import UroborosEngine

load_dotenv()

app = FastAPI(title="Ouroboros API")

# フロントエンドからのリクエスト形式を定義
class QueryRequest(BaseModel):
    query: str
    genre: str = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = UroborosEngine()

@app.get("/")
def read_root():
    return {"message": "Welcome to Ouroboros API - RAG Mode Active"}

@app.post("/generate-from-index")
async def generate_from_index(request: QueryRequest):
    """
    インデックス済みの論文からクエリに基づいた構成図を生成する
    """
    try:
        # ユーザーのクエリを元に、Azure AI Search 経由で図解を生成
        mermaid_code = await engine.generate_architecture(request.query)

        return {
            "query": request.query,
            "mermaid": mermaid_code,
            "summary": f"インデックスから『{request.query}』に関する情報を抽出して図解しました。",
        }
    except Exception as e:
        # エンジン内部で起きた Connection error などをここでキャッチ
        print(f"API ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))