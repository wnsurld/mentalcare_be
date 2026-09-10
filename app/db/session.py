# app/db/session.py
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ── 환경변수에서 DSN/로깅 읽기 ─────────────────────────────────────────────
# 예) postgresql+psycopg://USER:PASS@HOST:PORT/DBNAME

load_dotenv()  # .env 파일 로드

DATABASE_URL = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL / DATABASE_URL_SYNC 환경변수가 설정되지 않았습니다.")
# 개발 중 SQL 로그 보고 싶으면 환경변수로 켜기: set DEBUG_SQL=1
DEBUG_SQL = os.getenv("DEBUG_SQL", "0") == "1"

# ── 엔진 생성(동기) ───────────────────────────────────────────────────────
# pool_pre_ping: 죽은 커넥션 자동 감지/대체
# pool_recycle: 오래된 커넥션 주기적으로 재생성(초)
# pool_size/max_overflow: 서비스 규모에 맞게 조정
# connect_args: 세션 타임존 Asia/Seoul 고정
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
    future=True,
    connect_args={"options": "-c timezone=Asia/Seoul"},
    echo=DEBUG_SQL,
)

# ── 세션 팩토리 ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# ── FastAPI Depends에서 쓰는 요청 단위 세션 ──────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI DI용 동기 세션. 요청 시작~종료 동안 1개 세션을 안전하게 유지/종료합니다.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── 배치/스크립트용 컨텍스트 매니저(선택) ────────────────────────────────
@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    with db_session() as db: 형태로 쓰는 동기 세션 컨텍스트 매니저.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
