import os
import uuid
import datetime
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from services.uroboros_engine import UroborosEngine
from services.cosmos_manager import cosmos_manager

load_dotenv()

app = FastAPI(title="Ouroboros API")


# フロントエンドからのリクエスト形式を定義
class QueryRequest(BaseModel):
    query: str
    genre: str = None


raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
origins = [origin.strip() for origin in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["Content-Type", "X-Ouroboros-Key", "Authorization"],
    max_age=600,
)

engine = UroborosEngine()


async def verify_password(x_ouroboros_key: str = Header(None)):
    expected_key = os.getenv("APP_PASSWORD")
    if x_ouroboros_key != expected_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid System Key")
    return x_ouroboros_key


@app.get("/")
def read_root():
    return {"message": "Welcome to Ouroboros API - RAG Mode Active"}


@app.post("/generate-from-index")
async def generate_from_index(
    request: QueryRequest,
    key: str = Depends(verify_password),
):
    """
    インデックス済みの論文からクエリに基づいた構成図を生成し、結果をCosmos DBに保存する
    """
    try:
        # ユーザーのクエリを元に、Azure AI Search 経由で図解を生成
        mermaid_code = await engine.generate_architecture(request.query)

        # Cosmos DBに保存するデータを作成
        item_to_save = {
            "id": str(uuid.uuid4()),
            "query": request.query,
            "mermaid": mermaid_code,
            "summary": f"インデックスから『{request.query}』に関する情報を抽出して図解しました。",
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

        # Cosmos DBに保存
        await cosmos_manager.add_item(item_to_save)

        return item_to_save

    except Exception as e:
        # エンジン内部で起きた Connection error などをここでキャッチ
        print(f"API ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(key: str = Depends(verify_password)):
    """
    Cosmos DBから履歴を取得する
    """
    try:
        items = await cosmos_manager.get_items()
        return items
    except Exception as e:
        print(f"API ERROR (get_history): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(item_id: str, key: str = Depends(verify_password)):
    """
    指定されたIDの履歴をCosmos DBから削除する
    """
    try:
        await cosmos_manager.delete_item(item_id)
        return
    except Exception as e:
        print(f"API ERROR (delete_history_item): {e}")
        # ここではアイテムが見つからない場合も考慮できるが、シンプルに500を返す
        raise HTTPException(status_code=500, detail=str(e))
