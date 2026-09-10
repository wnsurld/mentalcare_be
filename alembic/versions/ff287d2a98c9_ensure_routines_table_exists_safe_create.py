from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "ff287d2a98c9"  # 자동 생성된 값 그대로
down_revision = "ad93f2863147"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    routines 테이블이 없으면 새로 만들고,
    이미 있으면 아무 것도 하지 않는다.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("routines"):
        op.create_table(
            "routines",
            # PK: routine_id (텍스트 슬러그)
            sa.Column("routine_id", sa.Text(), primary_key=True),

            sa.Column("source_doc_id", sa.Text(), nullable=True),
            sa.Column("source_url", sa.Text(), nullable=True),

            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("goal", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),

            sa.Column(
                "target_emotions",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),
            sa.Column(
                "target_situations",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),

            sa.Column("routine_type", sa.Text(), nullable=True),
            sa.Column("difficulty", sa.Text(), nullable=True),
            sa.Column("duration_min", sa.Integer(), nullable=True),

            sa.Column(
                "environment",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),
            sa.Column(
                "required_tools",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),

            sa.Column(
                "steps",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),
            sa.Column(
                "safety_notes",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),

            sa.Column(
                "tags",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default="{}",
            ),
            sa.Column(
                "language",
                sa.Text(),
                nullable=False,
                server_default="ko",
            ),

            sa.Column("embedding", Vector(768), nullable=True),
        )
    else:
        # 이미 routines 테이블이 있는 경우:
        # 여기서 스키마를 강제로 건드리지 않고 그냥 통과시킨다.
        # (나중에 여유 생기면 ALTER TABLE로 정리)
        pass


def downgrade() -> None:
    """
    롤백 시 routines 테이블이 있을 때만 삭제.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("routines"):
        op.drop_table("routines")
