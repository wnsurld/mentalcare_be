"""UPDATE_routine_vector_index

Revision ID: d587dc53ce51
Revises: fd45764072cf
Create Date: 2025-11-26 12:20:23.750424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd587dc53ce51'
down_revision: Union[str, Sequence[str], None] = 'fd45764072cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 코사인 기준 ivfflat 인덱스 예시 (연산자는 rag_service와 통일)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_routines_embedding_ivfflat
        ON routines
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_routines_embedding_ivfflat;")
