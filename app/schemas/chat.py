# app/schemas/chat.py
from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Any, Union, Literal, Optional, List


# ---- 1) 세션 생성 응답 ----
class ChatResponse(BaseModel):
    session_id: UUID


# ---- 2) /{session_id}/message 요청 바디 ----
class SendMessageRequest(BaseModel):
    user_msg: str
    flag: int  # 0: plain, 1: RAG 재수행 요청


# ---- 3) RAG에서 "정보 더 필요"일 때 ----
class NeedMoreInfoResponse(BaseModel):
    msg: str
    flag: Literal[1]
    can_create_report: bool


# ---- 4) compose 결과 스키마 ----
class ComposeResult(BaseModel):
    message: str
    routine_draft: str
    user_profile: Dict[str, Any]

class RoutineCard(BaseModel):
    """
    프론트에서 사용하는 '루틴 카드' 스키마.
    - id: DB routines.routine_id
    - title: 루틴 제목
    - steps: 실행 단계
    - why: 이 루틴이 왜 도움이 되는지 설명 (description에서 파생)
    - duration_min: 예상 소요 시간(분) – 아직 DB에 없으므로 Optional
    """
    id: str
    title: str
    steps: List[str] = []
    why: Optional[str] = None
    duration_min: Optional[int] = None


class RagSuccessResult(BaseModel):
    """
    flag=0 (RAG 성공)일 때 result 필드의 형태.
    """
    message: str
    card: Optional[RoutineCard] = None


# ---- 5) RAG 성공 응답 ----
class RagSuccessResponse(BaseModel):
    """
    RAG 성공 응답.
    - result.message: 사용자에게 보여줄 전체 답변
    - result.card: UI에서 사용할 대표 루틴 카드 1개
    """
    result: RagSuccessResult
    flag: Literal[0]
    can_create_report: bool



# ---- 6) plain LLM 응답 ----
class PlainLLMResponse(BaseModel):
    msg: str


# ---- 7) send_message 공통 응답 타입 ----
SendMessageOutput = Union[
    NeedMoreInfoResponse,
    RagSuccessResponse,
    PlainLLMResponse,
]


# ---- 8) (선택) /api/chat/rag 같은 다른 엔드포인트용 ----
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_msg: str

# ---- 9) 세션 종료 응답 (/api/chat/{session_id}/end) ----
class EndSessionResponse(BaseModel):
    status: str  # 예: "success"