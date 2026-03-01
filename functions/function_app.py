import io
import uuid
import logging
from datetime import datetime, timezone
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_settings import BaseSettings, SettingsConfigDict


# 設定管理クラス
class Settings(BaseSettings):
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_embedding_deployment: str
    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index_name: str
    azure_storage_connection_string: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


class UroborosBatchLoader:
    def __init__(self):
        self.container_name = "knowledge-base"
        self.aoai_model = settings.azure_openai_embedding_deployment

    async def run_automated_indexing(self):
        """Blobをスキャンして新規/更新ファイルをインデックス化する"""
        blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        container_client = blob_service_client.get_container_client(self.container_name)

        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=AzureKeyCredential(settings.azure_search_key),
        )

        embed_client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version="2024-02-01",
        )

        # 1. Blob内を再帰的にスキャン
        blobs = container_client.list_blobs()
        for blob in blobs:
            if not blob.name.endswith(".pdf"):
                continue

            logging.info(f"Processing: {blob.name}")

            # 2. パスからジャンルとサブジャンルを抽出
            # it/paper/xxx.pdf -> ["it", "paper", "xxx.pdf"]
            path_parts = blob.name.split("/")
            genre = path_parts[0] if len(path_parts) > 1 else "general"
            sub_genre = path_parts[1] if len(path_parts) > 2 else "uncategorized"

            # 3. PDFのダウンロードとテキスト抽出
            blob_client = container_client.get_blob_client(blob)
            stream = io.BytesIO(blob_client.download_blob().readall())
            doc = fitz.open(stream=stream, filetype="pdf")
            full_text = "".join([page.get_text() for page in doc])

            # 4. チャンク分割 (RecursiveCharacterTextSplitterを使用)
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=100
            )
            chunks = splitter.split_text(full_text)

            # 5. ベクトル化とアップロード
            batch_docs = []
            parent_id = str(uuid.uuid4())

            for i, chunk in enumerate(chunks):
                # Embedding生成
                embed_res = embed_client.embeddings.create(
                    input=[chunk], model=self.aoai_model
                )
                vector = embed_res.data[0].embedding

                batch_docs.append(
                    {
                        "chunk_id": f"{parent_id}_{i}",
                        "parent_id": parent_id,
                        "content": chunk,
                        "content_vector": vector,
                        "genre": genre,
                        "sub_genre": sub_genre,
                        "source_path": blob.name,
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                    }
                )

            # Azure AI Searchへ送信
            if batch_docs:
                search_client.upload_documents(documents=batch_docs)
                logging.info(
                    f"Successfully indexed {len(batch_docs)} chunks from {blob.name}"
                )


# 毎週土曜日の 15:00 UTC (日本時間 日曜 0:00) に実行
@app.timer_trigger(
    schedule="0 0 15 * * Sat",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=True,
)
async def timer_trigger_ouroboros(myTimer: func.TimerRequest) -> None:
    logging.info("Python timer trigger function started.")
    loader = UroborosBatchLoader()
    await loader.run_automated_indexing()
    logging.info("Python timer trigger function finished.")
