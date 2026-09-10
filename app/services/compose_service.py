# app/services/compose_service.py

from __future__ import annotations

from typing import Dict, Any, List, Optional
import json

from app.core.prompt_loader import load_prompt
from app.services.gemini_client import client

from google.genai import types


def compose(
    routine_draft: Dict[str, Any],
    user_profile: Dict[str, Any] | None = None,
    emotion_cues: Optional[List[str]] = None,
    prompt_name: str = "empathetic_reply_v1",
) -> Dict[str, Any]:
    """
    compose 단계:

    - routine_draft: 대표 루틴 1개에 대한 구조화된 정보
      {
        "title": str,
        "duration_min": int | None,
        "steps": [str, ...],
        "why": str
      }

    - user_profile: {"name": ..., "tone_pref": ...} 같은 것
    - emotion_cues: 인퍼런스에서 나온 감정 리스트 (옵션)

    empathetic_reply_v1 프롬프트 스펙에 맞게
    JSON payload를 보내고, 응답 JSON에서 message만 꺼낸다.
    """
    system_prompt = load_prompt("compose", prompt_name)

    profile = user_profile or {}

    payload: Dict[str, Any] = {
        "routine_draft": routine_draft,
        "user_profile": profile,
    }
    if emotion_cues is not None:
        payload["emotion_cues"] = emotion_cues

    user_content = json.dumps(payload, ensure_ascii=False)

    config = types.GenerateContentConfig(system_instruction=system_prompt)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_content)],
            )
        ],
        config=config,
    )

    raw_text = response.text or ""

    # 프롬프트는 JSON 출력을 요구하지만, 혹시 깨져 나올 수 있으니 방어적으로 처리
    message: str
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict) and "message" in parsed:
            message = str(parsed.get("message") or "")
        else:
            message = raw_text
    except Exception:
        message = raw_text

    # chat_service.generate_routine_response에서 composed["message"]만 쓰므로
    # 기존 인터페이스를 유지하면서 raw도 같이 남겨 둠.
    return {
        "message": message,
        "routine_draft": routine_draft,
        "user_profile": profile,
        "raw": raw_text,
    }
