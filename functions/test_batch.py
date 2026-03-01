import asyncio
import logging
from function_app import UroborosBatchLoader

# ログをコンソールに表示する設定
logging.basicConfig(level=logging.INFO)

async def main():
    print("--- [TEST] ウロボロス・バッチ処理を開始します ---")
    loader = UroborosBatchLoader()
    try:
        await loader.run_automated_indexing()
        print("--- [TEST] すべての処理が正常に完了しました！ ---")
    except Exception as e:
        print(f"--- [TEST] エラー発生: {e} ---")

if __name__ == "__main__":
    asyncio.run(main())