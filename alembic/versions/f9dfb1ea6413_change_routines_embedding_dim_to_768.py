"""change routines embedding dim to 768

Revision ID: f9dfb1ea6413
Revises: e49324c291e1
Create Date: 2025-11-24 21:57:31.820428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9dfb1ea6413'
down_revision: Union[str, Sequence[str], None] = 'e49324c291e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 기존 인덱스 먼저 삭제 (있으면)
    op.execute("DROP INDEX IF EXISTS ix_routines_embedding;")
    # embedding 컬럼 타입 변경: vector(1536) -> vector(768)
    op.execute("ALTER TABLE routines ALTER COLUMN embedding TYPE vector(768);")
    # 인덱스 다시 생성
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_routines_embedding "
        "ON routines USING ivfflat (embedding vector_cosine_ops);"
    )


def downgrade():
    # 다시 원래대로 되돌리는 로직 (있으면 좋으니까 넣어줌)
    op.execute("DROP INDEX IF EXISTS ix_routines_embedding;")
    op.execute("ALTER TABLE routines ALTER COLUMN embedding TYPE vector(1536);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_routines_embedding "
        "ON routines USING ivfflat (embedding vector_cosine_ops);"
    )