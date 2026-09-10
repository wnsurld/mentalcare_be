"""create rag_documents table

Revision ID: 664c9cbbfa73
Revises: ccbe9adfcc67
Create Date: 2025-11-24 19:32:30.639411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '664c9cbbfa73'
down_revision: Union[str, Sequence[str], None] = 'ccbe9adfcc67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rag_documents',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('doc_id', sa.Text(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('doc_type', sa.Text(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('emotions', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('situations', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('embedding', Vector(1536)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_id')
    )


def downgrade() -> None:
    # 확장은 환경 설정 성격이라 되돌리지 않음
    pass
