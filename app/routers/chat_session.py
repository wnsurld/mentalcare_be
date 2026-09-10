# app/routers/chat_sessions.py

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.chat_session import (
    ChatSessionSummary,
    ChatSessionDetail,
    InputItem,
)
from app.services.chat_session import (
    get_user_sessions,
    get_session_with_inputs,
)

router = APIRouter(prefix="/api/chat-sessions", tags=["chat-sessions"])


@router.get("", response_model=list[ChatSessionSummary])
def list_my_sessions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    내 세션 목록 조회 (최신순).
    """
    sessions = get_user_sessions(db, user)
    # Pydantic 모델이 orm_mode라서 그대로 리턴 가능
    return sessions


@router.get("/{session_id}", response_model=ChatSessionDetail)
def get_session_detail(
    session_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    특정 세션의 상세 + 그 안의 입력 목록 조회.
    """
    session = get_session_with_inputs(db, user, session_id)

    # inputs는 이미 시간순으로 정렬되어 있음
    # ChatSessionDetail(orm_mode=True)라서 그대로 반환 가능하지만,
    # 명시적으로 매핑하고 싶으면 아래처럼 할 수도 있음.
    return ChatSessionDetail(
        id=session.id,
        start_time=session.start_time,
        inputs=[
            InputItem(
                id=i.id,
                session_id=i.session_id,
                created_at=i.created_at,
                input_type=i.input_type.value,  # TEXT Enum → "TEXT"
                text_content=i.text_content,
            )
            for i in session.inputs
        ],
    )
