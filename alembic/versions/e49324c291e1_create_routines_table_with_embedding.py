"""create routines table with embedding

Revision ID: e49324c291e1
Revises: 2061f17ddeec
Create Date: 2025-11-24 20:45:42.495615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'e49324c291e1'
down_revision: Union[str, Sequence[str], None] = '2061f17ddeec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ✅ pgvector extension (한 번만 만들면 됨. 이미 있으면 무시)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ✅ routines 테이블 생성
    op.create_table(
        "routines",
        sa.Column("routine_id", sa.Text, primary_key=True),

        sa.Column("source_doc_id", sa.Text, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),

        sa.Column("title", sa.Text, nullable=False),
        sa.Column("goal", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),

        sa.Column("target_emotions", sa.ARRAY(sa.Text), nullable=True, server_default="{}"),
        sa.Column("target_situations", sa.ARRAY(sa.Text), nullable=True, server_default="{}"),

        sa.Column("routine_type", sa.Text, nullable=True),   # breathing / mindfulness / behavior ...
        sa.Column("difficulty", sa.Text, nullable=True),     # easy / moderate / hard
        sa.Column("duration_min", sa.Integer, nullable=True),

        sa.Column("environment", sa.ARRAY(sa.Text), nullable=True, server_default="{}"),
        sa.Column("required_tools", sa.ARRAY(sa.Text), nullable=True, server_default="{}"),

        sa.Column("steps", sa.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("safety_notes", sa.ARRAY(sa.Text), nullable=True, server_default="{}"),

        sa.Column("tags", sa.ARRAY(sa.Text), nullable=True, server_default="{}"),
        sa.Column("language", sa.Text, nullable=False, server_default="ko"),

        # ✅ 벡터 임베딩 (1536 차원)
        sa.Column("embedding", Vector(1536), nullable=True),
    )

    # ✅ 벡터 인덱스 (코사인 유사도용 ivfflat)
    #   - 실제로는 테이블에 embedding 데이터 꽤 채워진 후에 인덱스 만드는 게 좋지만,
    #     지금은 간단하게 같이 생성해둘게.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_routines_embedding "
        "ON routines USING ivfflat (embedding vector_cosine_ops);"
    )


def downgrade():
    # 인덱스부터 삭제 후 테이블 삭제
    op.execute("DROP INDEX IF EXISTS ix_routines_embedding;")
    op.drop_table("routines")
