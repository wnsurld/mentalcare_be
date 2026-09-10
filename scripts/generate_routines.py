# scripts/generate_routines.py

"""
tagged_docs_normalized.jsonl을 기반으로
(원문 텍스트를 프롬프트에 넣지 않고)
감정/상황 태그 + 토픽만 가지고 Gemini에 루틴 생성을 요청하고,
Routine 테이블 스키마에 맞는 JSONL을 생성하는 스크립트.

실행 예:
    (.venv) $ set GEMINI_API_KEY=...    # Windows
    (.venv) $ python -m scripts.generate_routines
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

import google.generativeai as genai

# ── 프로젝트 루트 경로 세팅 ───────────────────────────────
CUR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CUR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ── 입출력 경로 ───────────────────────────────────────────
NORMALIZED_JSONL_PATH = PROJECT_ROOT / "data" / "rag" / "tagged_docs_normalized.jsonl"

ROUTINES_DIR = PROJECT_ROOT / "data" / "routines"
ROUTINES_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_ROUTINES_JSONL_PATH = ROUTINES_DIR / "generated_routines.jsonl"

# ── 환경변수 로드 ─────────────────────────────────────────
load_dotenv(PROJECT_ROOT / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ── Gemini 초기화 ─────────────────────────────────────────
def init_gemini():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    genai.configure(api_key=GEMINI_API_KEY)
    # 필요하면 여기서 모델 이름을 조정 (예: "gemini-2.5-pro")
    model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config={
        "max_output_tokens": 4096,
        "temperature": 0.5,
        "response_mime_type": "application/json",
    }
)
    return model


# ── 프롬프트 템플릿 (텍스트 X, 태그/토픽 기반) ─────────────
ROUTINE_SYSTEM_PROMPT = """
You are an assistant that designs small, practical, non-clinical self-care routines
for daily emotional and mental health support.

You are given:
- A list of emotions (in Korean)
- A list of situations (in Korean)
- An optional topic or theme (e.g., 불안, 스트레스, 분노, 자존감 등)

You MUST output routines that:
- Are concrete and actionable (step-by-step)
- Are short (2~10 minutes)
- Are safe for general adults
- Do NOT provide any medical advice, diagnosis, or treatment
- Are suitable for general self-care, not clinical treatment

Output FORMAT:
Return ONLY a JSON array (list) of routine objects.
NO explanation, NO markdown.

Each routine object MUST have these fields:

- routine_id: string (will be overwritten later, can be temporary unique id)
- title: string
- goal: string
- description: string
- target_emotions: list of strings
- target_situations: list of strings
- routine_type: string  # e.g., "breathing", "mindfulness", "behavior", "cognitive"
- difficulty: string    # "easy" | "moderate" | "hard"
- duration_min: integer
- environment: list of strings
- required_tools: list of strings
- steps: list of strings
- safety_notes: list of strings
- tags: list of strings
- language: string  # "ko" or "en" etc.

Remember:
- language should be "ko" and all texts must be in Korean.
- Safety notes should always include gentle warnings for people with severe or long-lasting symptoms.
- Focus on general wellbeing and daily self-care, not on anything medical or clinical.
"""

ROUTINE_USER_PROMPT_TEMPLATE = """
다음은 루틴을 설계할 때 참고할 정보입니다.

[대상 감정 태그]
{emotions}

[대상 상황 태그]
{situations}

[관련 토픽/주제 (있으면)]
{topic}

위 정보를 바탕으로, 사용자가 일상에서 바로 따라할 수 있는
짧은 자기관리 루틴을 1~3개 설계해 주세요.

각 루틴은:
- 한국어로 작성
- 2~10분 내에 끝나는 규모
- 단계별로 매우 구체적이어야 함
- 호흡/마음챙김/행동/인지 등으로 유형을 나눔
- 의료적/임상적 조언은 피하고, 일반적인 웰빙과 자기관리 수준으로만 작성

출력은 오직 JSON 배열 형식만 반환하세요.
"""


# ── 유틸 ──────────────────────────────────────────────────
def load_normalized_docs(path: Path) -> List[Dict[str, Any]]:
    """
    정규화된 tagged_docs_normalized.jsonl 파일을 읽어서
    각 줄을 JSON으로 파싱한 리스트를 반환.
    """
    docs: List[Dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"정규화된 파일을 찾을 수 없습니다: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def extract_text_from_response(resp):
    if not resp or not getattr(resp, "candidates", None):
        return ""

    cand = resp.candidates[0]

    # 1) .text 필드 먼저 시도
    if getattr(resp, "text", None):
        return resp.text.strip()

    # 2) parts 전체 순회
    parts = cand.content.parts if hasattr(cand, "content") else []
    texts = []

    for p in parts:
        # text 타입
        if hasattr(p, "text") and p.text:
            texts.append(p.text)
        # function_call 타입
        if hasattr(p, "function_call"):
            fc = p.function_call
            # JSON 형태의 arguments 추출
            if hasattr(fc, "args"):
                texts.append(json.dumps(fc.args))

        # inline_data 타입
        if hasattr(p, "inline_data"):
            try:
                d = p.inline_data.data.decode("utf-8")
                texts.append(d)
            except:
                pass

    return "\n".join(texts).strip()


def clean_gemini_json(text: str) -> str:
    """
    Gemini가 종종 ```json ... ``` 형태로 코드를 감싸거나,
    앞뒤에 설명 문장을 넣는 경우가 있어 이를 제거하고
    JSON 배열 부분([ ... ])만 추출하는 함수.
    """

    text = text.strip()

    # 1) 코드블럭 제거
    if text.startswith("```"):
        lines = text.splitlines()
        cleaned = []
        for ln in lines:
            ls = ln.strip().lower()
            # ``` 또는 ```json 같은 시작줄 제거
            if ls.startswith("```"):
                continue
            if ls == "json":
                continue
            cleaned.append(ln)
        text = "\n".join(cleaned).strip()

    # 2) 텍스트 안에서 JSON array 범위만 추출
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1 and end > start:
        text = text[start: end + 1].strip()

    return text

def call_gemini_for_routines(
    model,
    emotion_labels: List[str],
    situation_labels: List[str],
    topic: str | None = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    감정/상황 태그 + 토픽만 가지고 Gemini에 루틴 생성을 요청하고,
    JSON 리스트 형태로 파싱하여 반환.

    비정상 응답은 ([], 실패사유)로 반환한다.
    """

    # 태그가 하나도 없으면 너무 애매하니 스킵
    if not emotion_labels and not situation_labels:
        return [], "감정/상황 태그 없음"

    topic_str = topic or ""

    user_prompt = ROUTINE_USER_PROMPT_TEMPLATE.format(
        emotions=", ".join(emotion_labels or []),
        situations=", ".join(situation_labels or []),
        topic=topic_str,
    )

    try:
        resp = model.generate_content(
            [ROUTINE_SYSTEM_PROMPT, user_prompt],
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=4096,
            ),
        )
    except Exception as e:
        return [], f"Gemini 호출 실패: {e}"

    if not getattr(resp, "candidates", None):
        pf = getattr(resp, "prompt_feedback", None)
        block_reason = getattr(pf, "block_reason", None) if pf else None
        return [], f"응답 후보 없음 (block_reason={block_reason})"

    raw_text = extract_text_from_response(resp)
    if not raw_text:
        return [], "응답에 텍스트가 없음"

    text = clean_gemini_json(raw_text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return [], f"JSON 파싱 실패: {e}"

    if not isinstance(data, list):
        return [], "응답이 리스트가 아님"

    if not data:
        return [], "루틴이 0개 생성됨"

    return data, None


# ── 메인 파이프라인 ──────────────────────────────────────
def main():
    model = init_gemini()
    docs = load_normalized_docs(NORMALIZED_JSONL_PATH)

    total_docs = len(docs)
    print(f"🔍 정규화된 문서 개수: {total_docs}")
    print(f"💾 생성된 루틴 JSONL 저장 경로: {GENERATED_ROUTINES_JSONL_PATH}")

    routine_count = 0
    success_docs = 0
    failed_docs: List[Tuple[Any, str]] = []

    with GENERATED_ROUTINES_JSONL_PATH.open("w", encoding="utf-8") as out_f:
        for idx, doc in enumerate(docs, start=1):
            doc_id = doc.get("doc_id")
            source_url = doc.get("source_url")
            emotion_labels = doc.get("emotion_labels") or []
            situation_labels = doc.get("situation_labels") or []
            topic = doc.get("topic") or doc.get("doc_type") or ""

            routines, fail_reason = call_gemini_for_routines(
                model=model,
                emotion_labels=emotion_labels,
                situation_labels=situation_labels,
                topic=topic,
            )

            if fail_reason:
                failed_docs.append((doc_id, fail_reason))
                print(f"[FAIL] doc_id={doc_id} ({idx}/{total_docs}) reason={fail_reason}")
                continue

            for r_idx, r in enumerate(routines, start=1):
                routine_obj = {
                    "routine_id": f"{doc_id}_r{r_idx}",
                    "source_doc_id": doc_id,
                    "source_url": source_url,
                    "title": r.get("title") or "",
                    "goal": r.get("goal") or "",
                    "description": r.get("description") or "",
                    "target_emotions": r.get("target_emotions") or emotion_labels,
                    "target_situations": r.get("target_situations") or situation_labels,
                    "routine_type": r.get("routine_type") or "behavior",
                    "difficulty": r.get("difficulty") or "easy",
                    "duration_min": r.get("duration_min") or 5,
                    "environment": r.get("environment") or [],
                    "required_tools": r.get("required_tools") or [],
                    "steps": r.get("steps") or [],
                    "safety_notes": r.get("safety_notes") or [],
                    "tags": r.get("tags") or [],
                    "language": r.get("language") or "ko",
                }
                out_f.write(json.dumps(routine_obj, ensure_ascii=False) + "\n")
                routine_count += 1

            success_docs += 1
            print(f"[SUCCESS] doc_id={doc_id} ({idx}/{total_docs}) routines={len(routines)} (total={routine_count})")

    print(f"\n🎉 완료: 총 {routine_count}개 루틴을 생성하여 {GENERATED_ROUTINES_JSONL_PATH} 에 저장했습니다.")
    print(f"✅ 성공 문서: {success_docs}개 | ⚠️ 실패/스킵 문서: {len(failed_docs)}개")
    if failed_docs:
        print("실패/스킵 사유 목록:")
        for doc_id, reason in failed_docs:
            print(f"  - doc_id={doc_id}: {reason}")


if __name__ == "__main__":
    main()
