# scripts/test_retrieve.py

import sys
from pathlib import Path

CUR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CUR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.services.rag_service import retrieve  # 네가 만든 함수 경로에 맞게 조정

def main():
    session = SessionLocal()
    try:
        query = "요즘 너무 불안하고 잠을 잘 못 자요. 특히 회사 일 때문에 스트레스가 심해요."
        print(f"🔍 query: {query}")
        result = retrieve(query, session)

        print("=== RAG 결과 ===")
        if not result or not result.get("docs"):
            print("❌ docs 없음 (retrieve가 아무 것도 못 찾음)")
            return

        docs = result["docs"]
        for i, doc in enumerate(docs, start=1):
            # doc 구조에 따라 수정 필요
            print(f"[{i}] routine_id={doc.get('routine_id')} | title={doc.get('title')} | score={doc.get('score')}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
