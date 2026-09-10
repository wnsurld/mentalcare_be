# scripts/test_rag_pipeline.py

import uuid

from app.db.session import SessionLocal
from app.services.chat_service import run_full_rag  # 실제 함수 경로에 맞게 수정

def main():
    db = SessionLocal()

    # 1️⃣ 세션 ID 아무거나
    session_id = str(uuid.uuid4())

    # 2️⃣ 테스트용 유저 입력 (RAG가 잘 먹을 만한 문장 하나)
    user_msg = "요즘 회사 일 때문에 스트레스가 너무 심하고, 성과 평가가 다가와서 불안해요. 잠도 잘 못 자요."

    # 3️⃣ 유저 프로필은 비워두거나 최소한만
    user_profile = {}

    # 4️⃣ 파이프라인 호출
    print("=== RAG 파이프라인 스모크 테스트 시작 ===")
    resp = run_full_rag(session_id=session_id, user_msg=user_msg, user_profile=user_profile, db=db)

    print("=== 결과 타입:", type(resp))
    print("=== 결과 내용:", resp)

    db.close()

if __name__ == "__main__":
    main()
