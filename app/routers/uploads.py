# app/routers/uploads.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.uploads import UploadTextRequest, UploadResponse
from app.services.uploads import create_text_input  # ✅ 여기로 변경

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


@router.post("/text", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_text(
    payload: UploadTextRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    [서비스 흐름]

    - 첫 요청(세션 없음): session_id 없이 오면
        → 새 ChatSession + 첫 Inputs(TEXT) 생성
        → session_id / input_id 반환

    - 이후 요청(세션 있음): session_id 포함해서 오면
        → 해당 세션에 TEXT Inputs만 추가

    ⚠️ 감정 추론 / 상황 인식 / RAG 는 하지 않는다.
       그건 /api/chat/{session_id}/message 에서 chat_service가 처리.
    """

    row = create_text_input(
        db=db,
        user=user,
        payload=payload,
    )

    return UploadResponse(
        input_id=row.id,                 # UUID
        session_id=row.session_id,       # UUID
        input_type=row.input_type,       # Enum(InputType)
        text=row.text_content,
    )


@router.get("/health")
def uploads_health():
    return {"ok": True}
