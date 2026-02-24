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
        # 1. LLMの設定 (LangChain)
        api_key_str = os.getenv("AZURE_OPENAI_API_KEY") or ""
        self.llm = AzureChatOpenAI(
            azure_deployment="gpt-4o",
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_KEY") or "",
            api_key=SecretStr(api_key_str),
        )

        # 2. Embedding用の設定 (Azure SDK)
        self.embed_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
        )

        # 3. AI Search クライアントの設定
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name="ouroboros_index",
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
        )

    async def _retrieve_context(self, query: str, top_k: int = 5):
        """ユーザーの問に関連する論文の断片を検索する"""
        # クエリをベクトル化
        embed_res = self.embed_client.embeddings.create(
            input=[query], model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        )
        query_vector = embed_res.data[0].embedding

        # ベクトル検索の実行
        vector_query = VectorizedQuery(
            vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector"
        )

        results = self.search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["content", "source_path"],
        )

        return "\n\n".join(
            [f"Source: {r['source_path']}\n{r['content']}" for r in results]
        )

    async def generate_architecture(self, user_query: str):
        """RAGを使用してMermaid図解を生成する"""
        # 1. 関連する論文コンテキストを取得
        context = await self._retrieve_context(user_query)

        # 2. プロンプトの組み立て（図解に特化）
        propmt = ChatPromptTemplate.from_template("""
        あなたは超一流のシステムアーキテクトです。
        提供された論文の情報を基に、その核となるアルゴリズムやシステムフローを
        Mermaid.jsの **graph TD** 形式で視覚化してください。

        【論文から抽出された関連コンテキスト】
        {context}

        【出力ルール】
        1. コードブロック内にMermaidコードのみ出力すること。
        2. ノードラベルは A["システム名"] のように引用符で囲むこと。
        3. 論文独自のアルゴリズムステップ（Graph構築、コミュニティ検出など）を明確に含めること。
        4. 出典としてどのファイルの情報に基づいているか、図の末尾に注釈を入れること。
        """)

        # 3. 実行
        chain = propmt | self.llm
        response = await chain.ainvoke({"context": context})

        return response.content
