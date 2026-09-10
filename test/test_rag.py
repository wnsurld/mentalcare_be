# test/test_rag.py
from dotenv import load_dotenv

from app.db.session import SessionLocal
from app.services.rag_service import run_rag_pipeline

load_dotenv()

def main():
    db = SessionLocal()
    try:
        query = "회사 업무 스트레스가 심할 때 도움이 되는 짧은 루틴이 필요해"
        rag = run_rag_pipeline(query, db)
        print("=== RAG result ===")
        if not rag:
            print("No routines found or rag_result is empty.")
            return

        print("\n[Routine Draft Preview]")
        print(rag["routine_draft"][:800])

        print("\n[Source Docs Count]")
        print(len(rag["source_docs"]))
    finally:
        db.close()

if __name__ == "__main__":
    main()
