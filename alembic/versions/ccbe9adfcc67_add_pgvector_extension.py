"""add pgvector extension

Revision ID: ccbe9adfcc67
Revises: 929aec5a7c97
Create Date: 2025-11-24 19:08:42.895883

"""
from typing import Sequence, Union
from pgvector.sqlalchemy import Vector
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccbe9adfcc67'
down_revision: Union[str, Sequence[str], None] = '929aec5a7c97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

def downgrade() -> None:
    # 확장은 다운그레이드에서 제거하지 않음
    pass
