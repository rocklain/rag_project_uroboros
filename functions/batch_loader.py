import os
import uuid
from datetime import datetime
from pypdf import PdfReader
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

# プロジェクトルートまたはカレントディレクトリの .env を読み込む
load_dotenv()

# --- 環境変数の取得 ---
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME")

# ガード節：設定漏れがあれば即座に停止
if not all([AOAI_KEY, AOAI_ENDPOINT, SEARCH_KEY]):
    raise ValueError(
        "Error: 環境変数が不足しています。.envファイルを確認してください。"
    )

# --- クライアント初期化 ---
search_client = SearchClient(
    SEARCH_ENDPOINT, SEARCH_INDEX, AzureKeyCredential(SEARCH_KEY)
)
aoai_client = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT, api_key=AOAI_KEY, api_version="2023-05-15"
)


def run_batch(file_path, genre="General", sub_genre="General"):
    """
    指定されたPDFを解析し、ベクトル化してAzure AI SearchにUpsertする
    """
    print(f"[*] Starting ingestion: {file_path} (Genre: {genre})")

    # 1. PDFからテキスト抽出
    reader = PdfReader(file_path)
    full_text = "\n".join(
        [page.extract_text() for page in reader.pages if page.extract_text()]
    )

    # 2. チャンク分割 (1000文字目安)
    chunk_size = 1000
    chunks = [
        full_text[i : i + chunk_size] for i in range(0, len(full_text), chunk_size)
    ]

    parent_id = str(uuid.uuid4())
    documents = []

    # 3. 各チャンクの処理
    for i, chunk in enumerate(chunks):
        # ベクトル化
        embed_res = aoai_client.embeddings.create(input=[chunk], model=AOAI_DEPLOYMENT)
        vector = embed_res.data[0].embedding

        # スキーマに合わせたドキュメント作成
        doc = {
            "chunk_id": f"{parent_id}-{i}",
            "parent_id": parent_id,
            "content": chunk,
            "content_vector": vector,
            "genre": genre,
            "sub_genre": sub_genre,
            "source_path": os.path.basename(file_path),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }
        documents.append(doc)

    # 4. Azure AI Searchへの一括アップロード
    search_client.upload_documents(documents)
    print(f"[+] Successfully uploaded {len(documents)} chunks.")


if __name__ == "__main__":
    target_pdf = r"C:\Users\リリー\Desktop\Ouroboros\functions\From Local to Global_ A Graph RAG Approach to Query-Focused  Summarization.pdf"
    run_batch(target_pdf, genre="RAG", sub_genre="Architecture")