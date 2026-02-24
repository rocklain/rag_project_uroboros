import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from app.services.uroboros_engine import UroborosEngine

load_dotenv()

app = FastAPI(title="Ouroboros API")


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
    return {"message": "Welcome to Ouroboros API"}


@app.post("/analyze")
async def analyze_paper(file: UploadFile = File(...)):
    """
    論文PDFを受け取り、構成図(Mermaid)を生成するメインエンドポイント
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="PDFファイルのみを受け付けています。"
        )
    try:
        pdf_bytes = await file.read()

        text = engine.extract_text_from_pdf(pdf_bytes)
        if not text:
            raise HTTPException(
                status_code=500, detail="PDFからテキストを抽出できませんでした。"
            )

        mermaid_code = await engine.generate_architecture(text)

        return {
            "filename": file.filename,
            "mermaid": mermaid_code,
            "summary": "解析が完了しました。Mermaid形式で出力します。",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-from-index")
async def generate_from_index(request: QueryRequest):
    """
    インデックス済みの論文から、クエリに基づいた構成図を生成する
    """
    try:
        # RAG 仕様の generate_architecture を呼び出す
        mermaid_code = await engine.generate_architecture(request.query)

        return {
            "query": request.query,
            "mermaid": mermaid_code,
            "summary": f"インデックスから『{request.query}に関する情報を抽出して図解しました。』",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
