import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index_name: str
    azure_openai_embedding_deployment: str
    azure_openai_chat_deployment: str
    
    # Cosmos DB Settings
    azure_cosmos_endpoint: str
    azure_cosmos_key: str
    azure_cosmos_database_name: str = "OuroborosDB"
    azure_cosmos_container_name: str = "History"


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore


class UroborosEngine:
    def __init__(self):
        print(f"DEBUG: AOAI ENDPOINT -> {settings.azure_openai_endpoint}")
        print(f"DEBUG: SEARCH ENDPOINT -> {settings.azure_search_endpoint}")
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.azure_openai_chat_deployment,
            api_version="2024-12-01-preview",
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=SecretStr(settings.azure_openai_api_key),
        )

        # 2. Embedding用の設定 (Azure SDK)
        self.embed_client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version="2024-02-01",
        )

        # 3. AI Search クライアントの設定
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=AzureKeyCredential(settings.azure_search_key),
        )

    async def _retrieve_context(self, query: str, top_k: int = 5):
        """ユーザーの問に関連する論文の断片を検索する"""
        try:
            print("Step 1: Embedding start")
            embed_res = self.embed_client.embeddings.create(
                input=[query], model=settings.azure_openai_embedding_deployment
            )
            query_vector = embed_res.data[0].embedding

            print("Step 2: Search start")
            vector_query = VectorizedQuery(
                vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector"
            )

            # aio版（非同期）クライアントなので、リクエストを await で待機
            results = await self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["content", "source_path"],
            )

            # 結果は非同期イテレータとして返るため、async for でリスト化
            result_list = [r async for r in results]
            print(f"Step 3: Search finished. Found {len(result_list)} chunks.")

            return "\n\n".join(
                f"Source: {r.get('source_path', 'N/A')}\n{r.get('content', '')}"
                for r in result_list
            )
        except Exception as e:
            print(f"CRITICAL ERROR IN _retrieve_context: {e}")
            raise e

    async def generate_architecture(self, user_query: str):
        """RAGを使用してMermaid図解を生成する"""
        # 1. 関連する論文コンテキストを取得
        context = await self._retrieve_context(user_query)

        if not context:
            return "graph TD\n  A['情報が見つかりませんでした']"

        # 2. プロンプトの組み立て
        prompt = ChatPromptTemplate.from_template("""
        あなたは超一流のシステムアーキテクトです。
        提供された論文の情報を基に、その核となるアルゴリズムやシステムフローを
        Mermaid.jsの **graph TD** 形式で視覚化してください。

        【論文から抽出された関連コンテキスト】
        {context}

        【出力ルール】
        1. コードブロック内にMermaidコードのみ出力すること。
        2. 出典としてどのファイルの情報に基づいているか、図の末尾に注釈を入れること。
        """)

        # 3. 実行
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": context})

        return response.content
