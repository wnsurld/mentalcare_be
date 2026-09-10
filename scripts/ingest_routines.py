"""
data/routines/generated_routines.jsonl 파일을 읽어
routines 테이블에 upsert(있으면 업데이트, 없으면 생성)하는 스크립트.

실행 예:
    (.venv) $ python -m scripts.ingest_routines
"""

import sys
import json
from pathlib import Path

from sqlalchemy.orm import Session

# ── 프로젝트 루트 경로 ───────────────────────────────────
CUR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CUR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal  # type: ignore
from app.models.routine import Routine   # type: ignore

ROUTINES_JSONL_PATH = PROJECT_ROOT / "data" / "routines" / "generated_routines.jsonl"


def ingest_routines(jsonl_path: Path):
    if not jsonl_path.exists():
        raise FileNotFoundError(f"루틴 JSONL 파일을 찾을 수 없습니다: {jsonl_path}")

    session: Session = SessionLocal()
    try:
        count = 0

        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                rec = json.loads(line)
                routine_id = rec["routine_id"]

                # 🔧 기존: session.get(Routine, routine_id)  → PK(id: bigint)에 문자열 넣어서 에러
                # 🔧 수정: 비즈니스 키인 routine_id(Text) 기준으로 조회
                existing: Routine | None = (
                    session.query(Routine)
                    .filter(Routine.routine_id == routine_id)
                    .one_or_none()
                )

                if existing:
                    existing.source_doc_id = rec.get("source_doc_id")
                    existing.source_url = rec.get("source_url")
                    existing.title = rec.get("title")
                    existing.goal = rec.get("goal")
                    existing.description = rec.get("description")
                    existing.target_emotions = rec.get("target_emotions") or []
                    existing.target_situations = rec.get("target_situations") or []
                    existing.routine_type = rec.get("routine_type")
                    existing.difficulty = rec.get("difficulty")
                    existing.duration_min = rec.get("duration_min")
                    existing.environment = rec.get("environment") or []
                    existing.required_tools = rec.get("required_tools") or []
                    existing.steps = rec.get("steps") or []
                    existing.safety_notes = rec.get("safety_notes") or []
                    existing.tags = rec.get("tags") or []
                    existing.language = rec.get("language") or "ko"
                else:
                    routine = Routine(
                        routine_id=routine_id,
                        source_doc_id=rec.get("source_doc_id"),
                        source_url=rec.get("source_url"),
                        title=rec.get("title"),
                        goal=rec.get("goal"),
                        description=rec.get("description"),
                        target_emotions=rec.get("target_emotions") or [],
                        target_situations=rec.get("target_situations") or [],
                        routine_type=rec.get("routine_type"),
                        difficulty=rec.get("difficulty"),
                        duration_min=rec.get("duration_min"),
                        environment=rec.get("environment") or [],
                        required_tools=rec.get("required_tools") or [],
                        steps=rec.get("steps") or [],
                        safety_notes=rec.get("safety_notes") or [],
                        tags=rec.get("tags") or [],
                        language=rec.get("language") or "ko",
                    )
                    session.add(routine)

                count += 1
                if count % 50 == 0:
                    session.commit()
                    print(f"💾 중간 커밋: {count}개 처리 완료")

        session.commit()
        print(f"🎉 ingest 완료: 총 {count}개 루틴을 DB에 반영했습니다.")

    finally:
        session.close()


def main():
    ingest_routines(ROUTINES_JSONL_PATH)


if __name__ == "__main__":
    main()
