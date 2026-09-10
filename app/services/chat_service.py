# app/services/chat_service.py

import json
import logging
import redis

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from dotenv import load_dotenv
from google.genai import types

from app.core.prompt_loader import load_prompt
from app.services.gemini_client import client
from app.services.rag_service import run_rag_pipeline
from app.services.compose_service import compose
from app.services.inference_service import infer_emotion_and_situation
from app.schemas.chat import NeedMoreInfoResponse, RagSuccessResponse
from app.core.redis_client import redis_client
from app.models import Inputs
from sqlalchemy import select
from datetime import datetime



load_dotenv()

# 👉 로거 설정
logger = logging.getLogger(__name__)

# 👉 세션 상태 키 포맷
SESSION_STATE_KEY_PREFIX = "session:state:"

def select_primary_routine(routines: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    여러 후보 루틴 중 대표 루틴 1개를 선택하는 함수.

    지금은 '첫 번째 루틴'을 그대로 반환하지만,
    나중에 점수/카테고리/사용자 선호도 등을 반영한 전략으로 교체할 수 있게
    별도 함수로 분리해 둔다.
    """
    if not routines:
        return None
    return routines[0]

def _state_key(session_id: str) -> str:
    return f"{SESSION_STATE_KEY_PREFIX}{session_id}"


def load_session_state(session_id: str) -> dict:
    """
    Redis에 저장된 세션 상태 조회.
    - hgetall 결과 그대로 dict로 반환.
    - 에러 시 빈 dict.
    """
    key = _state_key(session_id)
    try:
        state = redis_client.hgetall(key) or {}
        return state
    except Exception as e:
        logger.exception(
            "[RAG][STATE] load_session_state failed | session_id=%s | error=%r",
            session_id,
            e,
        )
        return {}


def save_session_state(session_id: str, **kwargs) -> None:
    """
    세션 상태를 Redis에 저장.
    - dict/list는 JSON 문자열로 저장
    - 나머지는 str로 저장
    - last_updated_at 자동 갱신
    """
    key = _state_key(session_id)
    mapping: dict[str, str] = {}

    for k, v in kwargs.items():
        if v is None:
            continue
        if isinstance(v, (dict, list)):
            mapping[k] = json.dumps(v, ensure_ascii=False)
        else:
            mapping[k] = str(v)

    mapping["last_updated_at"] = datetime.utcnow().isoformat()

    try:
        redis_client.hset(key, mapping=mapping)
    except Exception as e:
        logger.exception(
            "[RAG][STATE] save_session_state failed | session_id=%s | error=%r | mapping=%r",
            session_id,
            e,
            mapping,
        )

def can_create_session_report(session_id: str) -> bool:
    """
    이 세션으로 '세션 리포트'를 만들어도 되는지 판단.

    조건:
      - 최소 한 번이라도 루틴 추천 성공(has_success == "1")
      - 마지막 상태가 성공(last_flag == "0")
    """
    state = load_session_state(session_id)

    # 루틴 성공 기록이 없으면 리포트 생성 불가
    if state.get("has_success") != "1":
        return False

    # 마지막 flag가 0(성공)일 때만 허용
    if state.get("last_flag") != "0":
        return False

    return True

# ============================================================
#  루틴 추천 파이프라인 (핵심 유즈케이스)
# ============================================================

from fastapi import HTTPException

EMOTION_CONF_THRESHOLD = 0.7
SITUATION_CLARITY_THRESHOLD = 0.7


def generate_routine_response(
    session_id: str,
    user_msg: str,
    user_profile: dict,
    db: Session,
):
    logger.info(
        "[RAG] generate_routine_response START | session_id=%s | msg_preview=%r",
        session_id,
        user_msg[:80],
    )

    # 1) 감정/상황 추론
    inference = infer_emotion_and_situation(
        user_msg=user_msg,
        user_profile=user_profile,
    )

    logger.info(
        "[RAG] inference DONE | session_id=%s | main_mood=%r | need_more_info(raw)=%r",
        session_id,
        inference.get("main_mood"),
        inference.get("need_more_info"),
    )

    # 1-0) mood_overview 구조화 (Redis + 리포트 공용으로 쓸 형태)
    mood_overview = {
        "main_mood": inference.get("main_mood"),
        "emotions": inference.get("emotions", []),
        "situations": inference.get("situations", []),
        "summary": inference.get("summary"),
    }

    # --- 신뢰도 기반 need_more_info 결정 ---
    raw_need = inference.get("need_more_info", False)

    # LLM의 플래그는 참고용으로만 유지
    if isinstance(raw_need, str):
        normalized = raw_need.strip().lower()
        llm_need = normalized in ("true", "yes", "y", "1")
    else:
        llm_need = bool(raw_need)

    # 점수 가져오기
    emotion_conf = inference.get("emotion_confidence")
    situation_clarity = inference.get("situation_clarity")

    has_scores = (emotion_conf is not None) or (situation_clarity is not None)

    def _to_float_or_default(x, default: float = 1.0) -> float:
        try:
            v = float(x)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, v))

    if has_scores:
        emotion_conf_f = _to_float_or_default(emotion_conf, 1.0)
        situation_clarity_f = _to_float_or_default(situation_clarity, 1.0)

        need_because_emotion = emotion_conf_f < EMOTION_CONF_THRESHOLD
        need_because_situation = situation_clarity_f < SITUATION_CLARITY_THRESHOLD

        need_more_info = need_because_emotion or need_because_situation

        logger.info(
            "[RAG] need_more_info_decision | session_id=%s | "
            "emotion_conf=%.3f | situation_clarity=%.3f | "
            "need_emotion=%r | need_situation=%r | llm_need=%r | final=%r",
            session_id,
            emotion_conf_f,
            situation_clarity_f,
            need_because_emotion,
            need_because_situation,
            llm_need,
            need_more_info,
        )
    else:
        # 구버전 프롬프트 호환: 점수가 없으면 LLM 플래그 그대로 사용
        need_more_info = llm_need
        logger.info(
            "[RAG] need_more_info_decision (legacy) | session_id=%s | "
            "llm_need=%r | final=%r",
            session_id,
            llm_need,
            need_more_info,
        )

    # helper: clarifying_question 필수 확보
    def _require_clarifying_question() -> str:
        cq = inference.get("clarifying_question")
        if not cq or not str(cq).strip():
            logger.error(
                "[RAG] clarifying_question missing while need_more_info=True | "
                "session_id=%s | inference=%r",
                session_id,
                inference,
            )
            raise HTTPException(
                status_code=500,
                detail="clarifying_question missing from inference result",
            )
        return str(cq).strip()

    # 1-1) 인퍼런스 단계에서 정보 부족 → 추가 질문 반환
    if need_more_info:
        clarifying_question = _require_clarifying_question()

        # 감정 상태 + flag 저장
        save_session_state(
            session_id,
            last_mood_overview=mood_overview,
            last_flag="1",
        )

        return NeedMoreInfoResponse(
            msg=clarifying_question,
            flag=1,
            can_create_report=False,
        )

 # 2) 추론된 요약을 RAG 질의로 사용
    rag_query = inference.get("summary") or user_msg
    logger.info(
        "[RAG] run_rag_pipeline START | session_id=%s | rag_query_preview=%r",
        session_id,
        rag_query[:100],
    )

    # 3) RAG 실행
    rag_result = run_rag_pipeline(rag_query, db)
    if not rag_result:
        # RAG에서 문서를 못 찾은 경우도 추가 정보 요청으로 처리
        clarifying_question = _require_clarifying_question()

        save_session_state(
            session_id,
            last_mood_overview=mood_overview,
            last_flag="1",
        )

        return NeedMoreInfoResponse(
            msg=clarifying_question,
            flag=1,
            can_create_report=False,
        )

    logger.info(
        "[RAG] run_rag_pipeline DONE | session_id=%s | draft_keys=%r",
        session_id,
        list(rag_result.keys()),
    )

    # 4-1) 후보 루틴 리스트
    candidate_routines: List[Dict[str, Any]] = rag_result.get("source_docs") or []

    # 방어코드: 이론상 여기서는 비어있을 수 없지만, 안전하게 체크
    if not candidate_routines:
        clarifying_question = _require_clarifying_question()
        save_session_state(
            session_id,
            last_mood_overview=mood_overview,
            last_flag="1",
        )
        return NeedMoreInfoResponse(
            msg=clarifying_question,
            flag=1,
            can_create_report=False,
        )

    # 대표 루틴 1개 선택 (옵션 B 그대로 사용)
    primary = select_primary_routine(candidate_routines)

    # 대표 루틴으로 routine_draft 구성 (empathetic_reply_v1 INPUT 스펙에 맞춤)
    routine_draft = {
        "title": primary.get("title") or "추천 루틴",
        "duration_min": None,  # 아직 DB에 duration이 없으므로 None
        "steps": primary.get("steps") or [],
        "why": primary.get("description") or "",
    }

    # 4-2) Compose (공감 멘트 / 설명 생성)
    composed = compose(
        routine_draft=routine_draft,
        user_profile=user_profile,
        # 필요하면 감정 리스트도 같이 넘김 (optional)
        emotion_cues=inference.get("emotions") or None,
    )
    logger.info(
        "[RAG] compose DONE | session_id=%s | message_len=%d",
        session_id,
        len(composed.get("message", "")),
    )

    # 4-3) 루틴 요약(routine_overview) 구조화 (리포트용)
    routine_overview = {
        "has_routine": bool(candidate_routines),
        "items": [
            {
                "routine_id": r.get("routine_id"),
                "title": r.get("title"),
                "tags": r.get("tags") or [],
                "target_emotions": r.get("target_emotions") or [],
                "target_situations": r.get("target_situations") or [],
            }
            for r in candidate_routines
        ],
    }

    # ---------------------------------------------------------------
    # ✅ DB 저장 파트 (가장 최신 Input 1개에 결과 매핑)
    # ---------------------------------------------------------------
    try:
        input_row = (
            db.execute(
                select(Inputs)
                .where(Inputs.session_id == session_id)
                .order_by(Inputs.created_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        if input_row:
            # 1) 감정/상황 추론 전체 결과 저장
            input_row.inference_result = inference

            # 2) RAG 메타 저장
            meta = input_row.meta or {}
            meta.update(
                {
                    "rag_used": True,
                    # 후보 루틴들의 ID 리스트 (routine_id 기준)
                    "routine_ids": [
                        r.get("routine_id")
                        for r in candidate_routines
                        if r.get("routine_id") is not None
                    ],
                    "rag_sources": candidate_routines,
                }
            )
            input_row.meta = meta

            db.add(input_row)
            db.commit()
            db.refresh(input_row)

            logger.info(
                "[RAG][DB] updated Inputs | session_id=%s | input_id=%s",
                session_id,
                input_row.id,
            )
        else:
            logger.warning(
                "[RAG][DB] NO INPUT ROW FOUND | session_id=%s",
                session_id,
            )
    except Exception as e:
        logger.exception(
            "[RAG][DB] ERROR while updating Inputs | session_id=%s | error=%r",
            session_id,
            e,
        )

    # 🔹 대표 루틴 1개 선택 (옵션 B)
    # (이미 primary가 있음)

    DEFAULT_DURATION_MIN = 5
    if primary:
        card = {
            "id": primary.get("routine_id"),
            "title": primary.get("title") or "추천 루틴",
            "steps": primary.get("steps") or [],
            "why": primary.get("description") or "",
            # duration_min은 아직 스키마/DB에 없으므로 None으로 둔다.
            "duration_min": primary.get("duration_min") or DEFAULT_DURATION_MIN,
        }
        # 대표 루틴 ID를 routine_overview에도 남겨두면,
        # 리포트에서 “실제로 추천된 루틴 1개”를 추적하기 좋다.
        routine_overview["primary_routine_id"] = card["id"]
    else:
        card = None

    # 🔹 세션 상태 저장: 루틴 추천까지 성공
    now = datetime.utcnow().isoformat()
    save_session_state(
        session_id,
        last_flag="0",
        has_success="1",
        last_success_at=now,
        last_mood_overview=mood_overview,
        last_routine_overview=routine_overview,
    )

    # 5) Redis에 메세지 저장 (대화 로그)
    save_message(session_id, "assistant", composed["message"], db)

    logger.info(
        "[RAG] generate_routine_response DONE | session_id=%s | flag=0 | has_card=%s",
        session_id,
        bool(card),
    )

    # 🔹 최종 응답 페이로드 (RagSuccessResult 구조에 맞춤)
    result_payload = {
        "message": composed.get("message", ""),
        "card": card,
    }

    return RagSuccessResponse(
        result=result_payload,
        flag=0,
        can_create_report=True,
    )


def run_full_rag(session_id, user_msg, user_profile, db):
    """기존 라우터와 호환용 래퍼"""
    logger.info(
        "[RAG] run_full_rag WRAPPER | session_id=%s | msg_preview=%r",
        session_id,
        user_msg[:80],
    )
    return generate_routine_response(
        session_id=session_id,
        user_msg=user_msg,
        user_profile=user_profile,
        db=db,
    )


# ============================================================
#  Redis & 요약 관리
# ============================================================

async def send_message(session_id, message):
    redis_client.xadd(
        f"chat_stream:{session_id}",
        {"message": message}
    )


def save_message(session_id, role, content, db):
    key = f"chat:{session_id}:messages"
    message = {"role": role, "content": content}
    try:
        redis_client.rpush(key, json.dumps(message, ensure_ascii=False))
    except redis.RedisError as e:
        # logger 사용
        logger.error("❌ Redis error in save_message | session_id=%s | error=%r", session_id, e)


def summarize_message(session_id, key_msg, db):
    key_idx = f"session:summary_index:{session_id}"
    key_sum = f"session:summary:{session_id}"

    count = redis_client.llen(key_msg)
    last_idx_raw = redis_client.get(key_idx)
    last_idx = int(last_idx_raw) if last_idx_raw else -1

    logger.info(
        "[SUM] summarize_message START | session_id=%s | count=%d | last_idx=%d",
        session_id,
        count,
        last_idx,
    )

    msgs = [
        json.loads(m)
        for m in redis_client.lrange(key_msg, last_idx + 1, count - 1)
    ]

    if last_idx == -1:
        row = (
            db.query(Inputs)
            .filter(Inputs.session_id == session_id)
            .one()
        )
        first_input = row.text_content
        new_summary = summarize_llm(first_input, msgs)
    else:
        prev_summary = redis_client.get(key_sum) or ""
        new_summary = summarize_llm(prev_summary, msgs)

    redis_client.set(key_sum, new_summary)
    redis_client.set(key_idx, count - 1)

    logger.info(
        "[SUM] summarize_message DONE | session_id=%s | new_idx=%d",
        session_id,
        count - 1,
    )


def get_all_messages(session_id):
    key = f"chat:{session_id}:messages"
    raw_list = redis_client.lrange(key, 0, -1)
    return [json.loads(item) for item in raw_list]

# 유저 메세지 가져오기
def get_user_messages(session_id: str):
    all_messages = get_all_messages(session_id)
    user_messages = [m["content"] for m in all_messages if m["role"] == "user"]
    return user_messages

def get_sum_messages(session_id):
    key = f"session:summary:{session_id}"
    raw = redis_client.get(key)
    return raw if raw else None


# ============================================================
#  LLM 유틸 (Plain답변 & Summarizer)
# ============================================================

def plain_llm(session_id, user_msg, db):

    system_prompt = load_prompt(
        stage="compose",
        name="plain_empathetic_reply_v1",
    )

    config = types.GenerateContentConfig(system_instruction=system_prompt)
    
    logger.info(
        "[PLAIN] plain_llm START | session_id=%s | msg_preview=%r",
        session_id,
        user_msg[:80],
    )

    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(role="user", parts=[types.Part.from_text(text=user_msg)])
        ],
        config=config
    )

    msg = res.text
    save_message(session_id, "assistant", msg, db)

    logger.info(
        "[PLAIN] plain_llm DONE | session_id=%s | msg_len=%d",
        session_id,
        len(msg or ""),
    )
    return msg


def summarize_llm(prev_summary, msgs):
    new_msgs = "\n".join(f"{m['role']}: {m['content']}" for m in msgs)

    combined = f"""
[이전요약]
{prev_summary}

[새로운대화]
{new_msgs}
"""
    # ✅ 프롬프트 파일에서 로딩
    system_prompt = load_prompt(
        stage="analyze",
        name="session_incremental_summary_v1",
    )
    

    config = types.GenerateContentConfig(system_instruction=system_prompt)

    logger.info(
        "[SUM] summarize_llm START | prev_len=%d | num_msgs=%d",
        len(prev_summary or ""),
        len(msgs),
    )

    res = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=combined)])],
        config=config,
    )

    text = res.text

    logger.info(
        "[SUM] summarize_llm DONE | summary_len=%d",
        len(text or ""),
    )

    return text
