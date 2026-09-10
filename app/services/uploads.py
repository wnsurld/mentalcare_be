# app/services/uploads.py

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.uploads import UploadTextRequest
from app.models.input import Inputs
from app.models.enum import InputType  # TEXT / IMAGE / AUDIO Enum
from app.models.chat_session import ChatSession  # ✅ 세션 생성용


def create_text_input(
    db: Session,
    user,
    payload: UploadTextRequest,
) -> Inputs:
    """
    텍스트 업로드 비즈니스 로직:

    - (1) payload.session_id 가 없으면:
          → 새 ChatSession 생성
          → 그 session_id로 첫 Inputs(TEXT) 생성

    - (2) payload.session_id 가 있으면:
          → 해당 세션에 TEXT Inputs만 추가

    - 감정 추론 / 상황 인식 / RAG 는 절대 여기서 안 함.
      (그건 전부 chat_service 쪽 책임)
    """

    # 0) 공통 validation
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    if user is None or getattr(user, "id", None) is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    # 1) 세션 결정
    session_id = payload.session_id

    if session_id is None:
        # ✅ 첫 메시지 → 새로운 ChatSession 생성
        session = ChatSession(user_id=user.id)
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    else:
        # ✅ 기존 세션 검증 (선택 사항이지만 최소한 존재 여부는 보는게 안전)
        session = db.get(ChatSession, session_id)
        if session is None or session.user_id != user.id:
            raise HTTPException(status_code=404, detail="session not found")

    # 2) Inputs 생성
    row = Inputs(
        user_id=user.id,
        session_id=session_id,
        input_type=InputType.TEXT,
        text_content=payload.text,
        meta=payload.meta or {},
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return row
