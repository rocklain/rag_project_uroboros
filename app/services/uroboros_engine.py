import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr
from dotenv import load_dotenv

load_dotenv()


class UroborosEngine:
    def __init__(self):
        # --- 共通の環境変数を取得 ---
        aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        aoai_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        search_key = os.getenv("AZURE_SEARCH_KEY", "")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "")

        print(f"DEBUG: AOAI ENDPOINT -> {aoai_endpoint}")
        print(f"DEBUG: SEARCH ENDPOINT -> {search_endpoint}")

        # 1. LLMの設定 (LangChain)
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
            api_version="2024-12-01-preview",
            azure_endpoint=aoai_endpoint,
            api_key=SecretStr(aoai_key),
        )

        # 2. Embedding用の設定 (Azure SDK)
        self.embed_client = AzureOpenAI(
            azure_endpoint=aoai_endpoint,
            api_key=aoai_key,
            api_version="2024-02-01",
        )

        # 3. AI Search クライアントの設定
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_key),
        )

    async def _retrieve_context(self, query: str, top_k: int = 5):
        """ユーザーの問に関連する論文の断片を検索する"""
        try:
            print("Step 1: Embedding start")
            embed_res = self.embed_client.embeddings.create(
                input=[query], model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")
            )
            query_vector = embed_res.data[0].embedding

            print("Step 2: Search start")
            vector_query = VectorizedQuery(
                vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector"
            )

            # search() 自体は非同期ではないので await しない
            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=["content", "source_path"],
            )

            # ここでリスト化する瞬間に Azure への通信が発生する
            result_list = list(results)
            print(f"Step 3: Search finished. Found {len(result_list)} chunks.")

            return "\n\n".join(
                [f"Source: {r['source_path']}\n{r['content']}" for r in result_list]
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
