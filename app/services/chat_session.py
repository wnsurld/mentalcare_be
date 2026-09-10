# app/services/chat_session.py

from uuid import UUID as UUIDType

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession
from app.models.input import Inputs


def get_user_sessions(db: Session, user) -> list[ChatSession]:
    """
    현재 사용자(user)의 모든 세션을 최신순으로 조회.
    """
    if user is None or getattr(user, "id", None) is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    q = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.start_time.desc())
    )
    return q.all()


def get_session_with_inputs(
    db: Session,
    user,
    session_id: UUIDType,
) -> ChatSession:
    """
    특정 세션 + 그 세션에 속한 모든 Inputs를 created_at 기준 오름차순으로 조회.
    """
    if user is None or getattr(user, "id", None) is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,  # 자신의 세션만 조회 가능
        )
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    # 세션에 속한 inputs를 시간순으로 정렬해서 미리 로딩
    session.inputs = (
        db.query(Inputs)
        .filter(Inputs.session_id == session.id)
        .order_by(Inputs.created_at.asc())
        .all()
    )

    return session
