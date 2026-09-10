# app/models/reports.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import ForeignKey, TIMESTAMP, text, Date, UniqueConstraint, Index, desc
from datetime import datetime, date
from app.db.base_class import Base
from typing import List


class SessionReport(Base):
    __tablename__ = "session_reports"

    report_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # 기존 conversation_id → session_id 로 통일
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),  # ← FK 대상 통일
        unique=True,
        nullable=False,
    )

    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    highlights: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    mood_overview: Mapped[dict] = mapped_column(JSONB, nullable=False)
    routine_overview: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )

    # ChatSession과의 관계 (세션당 리포트 1개 가정)
    session = relationship("ChatSession", back_populates="session_report", lazy="joined")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start_date"),
        Index("ix_weekly_reports_user_week_desc", "user_id", desc("week_start_date")),
    )

    weekly_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    week_info: Mapped[str] = mapped_column(nullable=False)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    mood_distribution: Mapped[list] = mapped_column(JSONB, nullable=False)
    weekly_mood_analysis: Mapped[dict] = mapped_column(JSONB, nullable=False)
    mood_manage_tip: Mapped[str] = mapped_column(nullable=False)
    positive_highlights: Mapped[str] = mapped_column(nullable=False)
    routine_overview: Mapped[list] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )

    user = relationship("Users", back_populates="weekly_reports", lazy="joined")
