# scripts/embed_routines.py

"""
routines 테이블에서 embedding 이 NULL 인 row들에 대해
Gemini text-embedding-004 임베딩을 생성해 저장하는 스크립트.

실행 예:
    (.venv) $ set GEMINI_API_KEY=...
    (.venv) $ python scripts/embed_routines.py
"""

import os
import sys
from typing import List
from pathlib import Path
from dotenv import load_dotenv

import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import select

# ── 프로젝트 루트 경로 ───────────────────────────────────
CUR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CUR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal  # type: ignore
from app.models.routine import Routine   # type: ignore

load_dotenv(PROJECT_ROOT / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def init_embedding_client():
    """GenAI 설정 (모델 인스턴스 X, 전역 설정만)."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    genai.configure(api_key=GEMINI_API_KEY)


def get_routine_embedding(text: str) -> List[float]:
    """
    text-embedding-004 임베딩 생성.
    google.generativeai 최신 버전에서는
    genai.embed_content(...) 를 top-level 으로 호출해야 함.
    """
    resp = genai.embed_content(
        model="models/text-embedding-004",  # 또는 "text-embedding-004" (둘 다 동작)
        content=text,
        task_type="RETRIEVAL_DOCUMENT",     # 선택이지만 RAG용이면 붙여주는 게 좋음
    )

    # resp 예: {"embedding": [ ... 768 floats ... ]}
    vec = resp["embedding"]
    if len(vec) != 768:
        raise ValueError(f"임베딩 차원 오류: {len(vec)} (expected 768)")
    return vec


def main(only_empty: bool = True, batch_size: int = 50):
    init_embedding_client()
    session: Session = SessionLocal()

    try:
        # 대상 row 선택
        if only_empty:
            stmt = select(Routine).where(Routine.embedding.is_(None))
        else:
            stmt = select(Routine)

        routines = session.execute(stmt).scalars().all()
        total = len(routines)
        print(f"🔍 임베딩 업데이트 대상 Routine 개수: {total} (only_empty={only_empty})")

        if total == 0:
            print("✅ 업데이트할 Routine 이 없습니다.")
            return

        updated = 0

        for i, r in enumerate(routines, start=1):
            # title + description + steps 합쳐서 임베딩
            base_text_parts = [r.title or "", r.description or ""]
            if r.steps:
                # JSON / ARRAY(Text) 라면 join 해서 하나의 텍스트로
                base_text_parts.append("\n".join(r.steps))

            base_text = "\n\n".join([p for p in base_text_parts if p.strip()])

            if not base_text.strip():
                print(f"- routine_id={r.routine_id} 에 텍스트 없음 → 스킵")
                continue

            vec = get_routine_embedding(base_text)
            r.embedding = vec
            updated += 1

            if i % batch_size == 0:
                session.commit()
                print(f"💾 중간 커밋: {i}/{total} 처리 완료 (업데이트 {updated}개)")

        session.commit()
        print(f"🎉 완료: 총 {total}개 중 {updated}개에 임베딩 저장 완료")

    finally:
        session.close()


if __name__ == "__main__":
    main()
