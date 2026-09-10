# app/models/chat_session.py
from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ChatSession(Base):
    """
    한 번의 대화 흐름(세션)을 표현하는 최소 테이블.

    - id: 세션 고유 ID (session_id 역할, UUID)
    - user_id: 세션 소유 사용자 UUID
    - message_ref_id:
        이 세션을 '시작시킨' 원본 입력(Inputs.id)을 가리키는 선택적 참조.
        서비스 레벨에서:
        - 새 세션 생성
        - 첫 Inputs row 생성
        - 그 Inputs.id를 message_ref_id에 채우는 흐름으로 사용.
    - start_time: 세션 시작 시각
    """

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),   # PostgreSQL: gen_random_uuid()
        comment="세션 고유 ID",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="세션 소유 사용자 UUID",
    )

    # 세션을 시작시킨 원문 메시지/입력의 ID(옵션).
    # 나중에 Inputs.id와 FK로 연결할 수 있지만, 지금은 UUID만 저장.
    message_ref_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,  # 나중에 메시지 테이블/Inputs와 FK를 강제하고 싶으면 FK + nullable=False로 변경 가능
        comment="세션의 원문 메시지/입력 참조 ID(옵션)",
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="세션 시작 시각",
    )

    # 관계: 한 세션에는 여러 Input이 속함
    inputs = relationship(
        "Inputs",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    # 세션 단위 리포트(요약/통계 등)를 1:1로 연결 (선택)
    session_report = relationship(
        "SessionReport",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user={self.user_id} start={self.start_time}>"
