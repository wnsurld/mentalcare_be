# alembic/env.py  — minimal, models: enum, user, chat_session, input, reports

from logging.config import fileConfig
import os, sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) 프로젝트 루트 경로 추가 (alembic/의 상위 디렉터리)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# 2) Base 메타데이터 (모든 모델 import는 app.db.base 내부에서 수행됨)
from app.db.base import Base  # <- base.py가 enum, user, chat_session, input, reports를 이미 import

# 3) Alembic 기본 설정
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# 4) DB URL (환경변수 DATABASE_URL이 있으면 우선)
def get_database_url() -> str:
    return os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

# 5) 마이그레이션 실행 (offline / online)
def run_migrations_offline():
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,            # 컬럼 타입 변화 감지
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {**config.get_section(config.config_ini_section, {}), "sqlalchemy.url": get_database_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
