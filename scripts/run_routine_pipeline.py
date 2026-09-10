# scripts/run_routine_pipeline.py

"""
정규화된 태깅 결과 → 루틴 생성 → DB ingest → 임베딩 생성
까지 한 번에 실행하는 파이프라인 스크립트.

실행 예:
    (.venv) $ set GEMINI_API_KEY=...
    (.venv) $ python -m scripts.run_routine_pipeline
"""

import sys
from pathlib import Path

CUR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CUR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.generate_routines import main as generate_main   # type: ignore
from scripts.ingest_routines import main as ingest_main       # type: ignore
from scripts.embed_routines import main as embed_main         # type: ignore


def main():
    print("=== 1/3: 루틴 자동 생성 (Gemini) ===")
    generate_main()

    print("\n=== 2/3: 생성된 루틴을 DB에 ingest ===")
    ingest_main()

    print("\n=== 3/3: routines.embedding NULL 대상 임베딩 생성 ===")
    embed_main(only_empty=True, batch_size=50)

    print("\n🎉 전체 루틴 파이프라인 완료!")


if __name__ == "__main__":
    main()
