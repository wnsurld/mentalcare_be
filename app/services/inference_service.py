# app/services/inference_service.py
from __future__ import annotations

from typing import Dict, Any
import os
import json
import logging

from app.core.prompt_loader import load_prompt
from app.services.gemini_client import client

from google.genai import types

logger = logging.getLogger(__name__)

def infer_emotion_and_situation(
    user_msg: str,
    user_profile: Dict[str, Any] | None = None,
    prompt_name: str = "emotion_situation_v1",
) -> Dict[str, Any]:
    """
    사용자의 원문 메시지(또는 요약 텍스트)를 기반으로
    감정/대표감정/상황/요약/추가질문 여부를 한 번에 추론한다.
    """

    profile = user_profile or {}
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)

    logger.info(
        "[infer] infer_emotion_and_situation START | "
        "text_preview=%r | profile_keys=%s",
        user_msg[:50],
        list(profile.keys()),
    )

    system_prompt = load_prompt("analyze", prompt_name) or ""

    user_message = f"""
[사용자 프로필]
{profile_json}

[사용자 원문 또는 요약 텍스트]
{user_msg}

위 정보를 기반으로, 사용자의 현재 상태를 아래 JSON 스키마에 맞춰 한국어로만 분석해 주세요.

반드시 순수 JSON만 출력하세요. 설명 텍스트, 마크다운, ```json``` 표기 등은 넣지 마세요.

요구 스키마:
{{
  "emotions": string[],                // 느껴지는 감정들 (예: ["불안", "짜증"])
  "main_mood": string | null,          // 대표 감정 한 단어 (예: "불안")
  "situations": string[],              // 사용자가 처한 상황/맥락 리스트
  "summary": string,                   // 1~2문장 요약 (사용자 상태/맥락)

  "emotion_confidence": number,        // 0.0~1.0: 감정 추론 신뢰도
  "situation_clarity": number,         // 0.0~1.0: 상황/맥락 이해도

  "need_more_info": boolean,           // (참고용) 현재 정보만으로 충분히 구체적인 루틴 추천이 가능한지 여부
  "clarifying_question": string | null,// 더 필요한 정보가 있다면, 사용자에게 물어볼 추가 질문 (없으면 null)
  "missing_info_reason": string | null // 왜 추가 정보가 필요한지 한 줄 설명 (없으면 null)
}}
"""

    config = types.GenerateContentConfig(
        system_instruction=system_prompt
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        ],
        config=config,
    )

    raw = (response.text or "").strip()
    logger.info(
        "[infer] LLM RAW RESPONSE | length=%d | preview=%r",
        len(raw),
        raw[:120],
    )

    # ```json ... ``` 포맷 방어
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].lstrip()
    if raw.endswith("```"):
        raw = raw[:-3].rstrip()

    # JSON 파싱
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(
            "[infer] JSONDecodeError in infer_emotion_and_situation: %s | raw_preview=%r",
            e,
            raw[:200],
        )
        parsed = {}

    emotions = parsed.get("emotions") or []
    if isinstance(emotions, str):
        emotions = [emotions]

    main_mood = parsed.get("main_mood") or (emotions[0] if emotions else None)

    situations = parsed.get("situations") or []
    if isinstance(situations, str):
        situations = [situations]

    summary = parsed.get("summary") or user_msg[:100]

    need_more_info = bool(parsed.get("need_more_info"))
    clarifying_question = parsed.get("clarifying_question") or None
    missing_info_reason = parsed.get("missing_info_reason") or None

    # --- 신뢰도 스코어 파싱 ---
    def _parse_score(x: Any, default: float = 1.0) -> float:
        try:
            v = float(x)
        except (TypeError, ValueError):
            return default
        if v < 0.0:
            v = 0.0
        if v > 1.0:
            v = 1.0
        return v

    emotion_confidence = _parse_score(parsed.get("emotion_confidence"), default=1.0)
    situation_clarity = _parse_score(parsed.get("situation_clarity"), default=1.0)

    result = {
        "emotions": emotions,
        "main_mood": main_mood,
        "situations": situations,
        "summary": summary,
        "need_more_info": need_more_info,
        "clarifying_question": clarifying_question,
        "missing_info_reason": missing_info_reason,
        "emotion_confidence": emotion_confidence,
        "situation_clarity": situation_clarity,
    }

    logger.info(
        "[infer] infer_emotion_and_situation DONE | main_mood=%r | "
        "emotions=%r | situations=%r | need_more_info=%r | "
        "emotion_confidence=%.3f | situation_clarity=%.3f",
        main_mood,
        emotions,
        situations,
        need_more_info,
        emotion_confidence,
        situation_clarity,
    )

    return result


def extract_emotion_llm(msg: str) -> str:
    """
    [호환용 래퍼] 기존 코드에서 쓰던 단일 감정 추출 함수를
    신규 infer_emotion_and_situation 기반으로 동작하게 함.
    """
    logger.info(
        "[infer] extract_emotion_llm START | text_preview=%r",
        msg[:50],
    )

    info = infer_emotion_and_situation(
        user_msg=msg,
        user_profile=None,
        prompt_name="emotion_situation_v1",
    )
    main_mood = info.get("main_mood") or (
        ", ".join(info.get("emotions", [])) if info.get("emotions") else ""
    )

    logger.info(
        "[infer] extract_emotion_llm DONE | main_mood=%r | emotions=%r",
        main_mood,
        info.get("emotions", []),
    )

    return main_mood
