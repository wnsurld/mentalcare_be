# app/routers/chat.py

import re
import json
import logging as logger
from app.core.redis_client import redis_client
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user

from app.schemas.chat import (
    SendMessageRequest,
    SendMessageOutput,
    PlainLLMResponse,
    NeedMoreInfoResponse,
    RagSuccessResponse,
    EndSessionResponse,
)

from app.models.chat_session import ChatSession
from app.models.input import Inputs
from app.models.reports import SessionReport

from app.services.chat_service import (
    run_full_rag,
    save_message,
    plain_llm,
    summarize_message,
    get_all_messages,
    get_sum_messages,
    load_session_state,          
    can_create_session_report,   
)

from app.services.inference_service import infer_emotion_and_situation
from app.services.generate_weekly_report import modify_llm

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ============================================================
#  1) 메시지 전송
# ============================================================
@router.post("/{session_id}/message", response_model=SendMessageOutput)
def send_message(
    session_id: str,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user_msg = payload.user_msg
    flag = payload.flag  # 0=루틴 생성 시도, 1=정보 보충

    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="not authorized")

    # 🔹 사용자 메시지 저장 (항상)
    save_message(session_id, "user", user_msg, db)

    # --------------------------------------------------------
    # 1) flag에 따라 RAG 입력 텍스트 구성
    #    - flag=0: 이번 user_msg만 사용
    #    - flag=1: 첫 입력 + 이번 입력 합치기
    # --------------------------------------------------------
    if flag == 1:
        first_input = (
            db.query(Inputs)
            .filter(Inputs.session_id == session_id)
            .order_by(Inputs.created_at.asc())
            .first()
        )

        if first_input is None:
            merged_input = user_msg
        else:
            merged_input = f"{first_input.text_content}\n\n{user_msg}"
    else:
        # flag == 0 (루틴 생성 시도)
        merged_input = user_msg

    # --------------------------------------------------------
    # 2) 항상 run_full_rag (RAG 파이프라인) 먼저 시도
    #    → generate_routine_response가
    #       - NeedMoreInfoResponse(flag=1, can_create_report=False)
    #       - RagSuccessResponse(flag=0, can_create_report=True)
    #      둘 중 하나를 돌려줌
    # --------------------------------------------------------
    try:
        result = run_full_rag(
            session_id=session_id,
            user_msg=merged_input,
            user_profile={"name": user.name},
            db=db,
        )
        return result

    except Exception as e:
        logger.exception(
            "[CHAT][send_message] run_full_rag failed | session_id=%s | error=%r",
            session_id,
            e,
        )

        # ----------------------------------------------------
        # 3) 완전 실패 시 fallback: plain_llm
        #    - 하지만 응답은 여전히 flag/can_create_report 포함한
        #      NeedMoreInfoResponse 형태로 맞춘다.
        # ----------------------------------------------------
        fallback_msg = plain_llm(session_id, user_msg, db)

        return NeedMoreInfoResponse(
            msg=fallback_msg,
            flag=1,              # "아직 확정 상태 아님 / 루틴 실패" 의미
            can_create_report=False,
        )

# ============================================================
#  2) 세션 종료 → 요약 + 감정 추출 + 리포트 저장
# ============================================================
# ============================================================
#  2) 세션 종료 → 요약 + 감정/루틴 정리 + 리포트 저장
# ============================================================
@router.post("/{session_id}/end", response_model=EndSessionResponse)
def end_session(
    session_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 0) 세션 존재 & 소유자 확인
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="not authorized")

    # 1) 이 세션으로 리포트를 만들어도 되는지 (flag + has_success 기반)
    if not can_create_session_report(session_id):
        raise HTTPException(
            status_code=400,
            detail="아직 루틴 추천이 완료되지 않아서 리포트를 만들 수 없어요. 먼저 분석을 마무리해 주세요.",
        )

    # 🔹 Redis 메시지 키 (save_message에서 사용한 것과 동일)
    key_msg = f"chat:{session_id}:messages"

    # 2) 최신 요약 한 번 더 수행 (증분 요약)
    summarize_message(session_id, key_msg, db)

    # 3) 전체 메시지 (추후 GCS 업로드용으로 남겨둠)
    all_msg = get_all_messages(session_id)
    all_msg_json = json.dumps(all_msg, ensure_ascii=False, indent=2)
    # TODO: all_msg_json → GCS 업로드 로직 추가 예정

    # 4) 최종 요약 텍스트 가져오기
    sum_msg = get_sum_messages(session_id) or ""
    

    # 5) Redis 세션 상태 로드 (mood/routine overview)
    state = load_session_state(session_id)

    # 5-1) mood_overview 가져오기 (없으면 fallback 인퍼런스)
    mood_overview = None
    raw_mood = state.get("last_mood_overview")
    if raw_mood:
        try:
            mood_overview = json.loads(raw_mood)
        except json.JSONDecodeError:
            logger.exception(
                "[END] failed to parse last_mood_overview JSON | session_id=%s | raw=%r",
                session_id,
                raw_mood,
            )

        if not mood_overview:
        # Redis에 없거나 파싱 실패 시: 요약 텍스트 기반으로 한 번 더 인퍼런스
            try:
                inference = infer_emotion_and_situation(
                    user_msg=sum_msg,
                    user_profile={"name": getattr(user, "name", None)},
                )
                mood_overview = {
                    "main_mood": inference.get("main_mood"),
                    "emotions": inference.get("emotions", []),
                    "situations": inference.get("situations", []),
                    "summary": inference.get("summary"),
                    "emotion_confidence": inference.get("emotion_confidence"),
                    "situation_clarity": inference.get("situation_clarity"),
                }
            except Exception as e:
                logger.exception(
                    "[END] infer_emotion_and_situation fallback failed | session_id=%s | error=%r",
                    session_id,
                    e,
                )
                mood_overview = {
                    "main_mood": None,
                    "emotions": [],
                    "situations": [],
                    "summary": None,
                    "emotion_confidence": None,
                    "situation_clarity": None,
                }


    # 5-2) routine_overview 가져오기 (없으면 기본값)
    routine_overview = None
    raw_routine = state.get("last_routine_overview")
    if raw_routine:
        try:
            routine_overview = json.loads(raw_routine)
        except json.JSONDecodeError:
            logger.exception(
                "[END] failed to parse last_routine_overview JSON | session_id=%s | raw=%r",
                session_id,
                raw_routine,
            )

    if not routine_overview:
        routine_overview = {
            "has_routine": False,
            "items": [],
        }

    # 결과물 다듬기
    stage = "report"
    
    # 1. 요약 다듬기
    name = "modify_summary"
    modify_sum = modify_llm(sum_msg, stage, name) 
    summary = {
        "text": modify_sum,
    }

    # 2. 하이라이트 다듬기
    joined_text = "\n".join(mood_overview["situations"])
    name = "modify_highlight"
    modify_situ = modify_llm(joined_text, stage, name)

    # 7) SessionReport upsert
    report = (
        db.query(SessionReport)
        .filter(SessionReport.session_id == session_id)
        .one_or_none()
    )

    if report is None:
        report = SessionReport(
            session_id=session_id,
            summary=summary,
            highlights=modify_situ,
            mood_overview=mood_overview["main_mood"],
            routine_overview=routine_overview,
        )
        db.add(report)
    else:
        report.summary = summary
        report.highlights = modify_situ
        report.mood_overview = mood_overview["main_mood"]
        report.routine_overview = routine_overview

    db.commit()

    return EndSessionResponse(status="success")