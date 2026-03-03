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

    from typing import Any

    def _sanitize_output(self, mermaid: Any) -> str:
        # mermaid は LLMからAny型で来ることがあるので文字列に変換
        text = str(mermaid)
        cleaned = text.replace("**", "").replace("`", "").replace("note1[", "")
        return cleaned

    def _validate_mermaid(self, mermaid: Any) -> bool:
        import re

        text = str(mermaid)  # 型エラー防止のため文字列化
        # サブグラフ名に直接矢印がつながってないか確認
        subgraphs = re.findall(r"subgraph\s+(\w+)", text)
        for sg in subgraphs:
            if re.search(rf"-->(\\s*){sg}", text):
                return False
        # check for naive note misuse
        if re.search(r"note\d+\[", text):
            return False

        # サブグラフ名に対して note が使われていないか確認
        for sg in subgraphs:
            # note (left|right|top|bottom) of <subgraph_name> を検出
            if re.search(rf"note\s+(?:left|right|top|bottom)\s+of\s+{sg}\b", text):
                return False

        return True

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
        3. サブグラフには直接矢印をつないではいけません。必ずサブグラフ内の個別ノードに接続すること。
        4. 注釈は `note <位置> of <ノード>:` の形式で出力すること。ただし、サブグラフ名に対して `note ... of` を使うことは禁止です。
        5. Markdown装飾(**など)を含めないこと。
        """)

        # 3. 実行／検証ループ
        chain = prompt | self.llm
        mermaid_code: str = ""
        current_context = context

        for attempt in range(3):
            response = await chain.ainvoke({"context": current_context})
            mermaid_code = str(response.content)
            if self._validate_mermaid(mermaid_code):
                return self._sanitize_output(mermaid_code)
            # 構文エラーが見つかった場合は注意文を追加してリトライ
            current_context += "\n\n# 前回の出力に構文エラーがありました。Mermaid構文に従い正しく修正してください。"
        # リトライ後もダメならクリーンアップして返す
        return self._sanitize_output(mermaid_code)
