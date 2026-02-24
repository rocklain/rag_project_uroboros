from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
import fitz
import os
from pydantic import SecretStr


class UroborosEngine:
    def __init__(self):
        api_key_str = os.getenv("AZURE_OPENAI_API_KEY") or ""
        self.llm = AzureChatOpenAI(
            azure_deployment="gpt-4o",
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT") or "",
            api_key=SecretStr(api_key_str),
        )

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """PDFバイナリからテキストを抽出する"""
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += str(page.get_text())
        return text

    async def generate_architecture(self, paper_text: str):
        prompt = ChatPromptTemplate.from_template("""
        あなたは超一流のシステムアーキテクトです。
        以下の論文（最新の生成AI研究）を読み、その手法を実際のアプリケーションとして実装する場合の
        「システム構成図」をMermaid.jsのgraph TD形式で作成してください。

        【論文内容】
        {paper_text}

        【出力ルール】
        1. コードブロック内にMermaidのコードのみを出力してください。
        2. 構成図には、Frontend, Backend, Database, AI Engine, External APIs等の要素を含めてください。
        3. 日本語で注釈を入れてください。
        4. Mermaidのノードラベルに日本語やHTMLタグを含める場合は、必ず A["ラベル名"] のようにダブルクォーテーションで囲んでください。
        """)

        chain = prompt | self.llm
        response = await chain.ainvoke({"paper_text": paper_text[:10000]})
        # トークン制限に注意
        return response.content
