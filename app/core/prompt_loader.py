# app/core/prompt_loader.py
from pathlib import Path

PROMPT_ROOT = Path(__file__).resolve().parent / "prompts"


def load_prompt(stage: str, name: str, role: str | None = None) -> str:
    if role == "safety":
        path = PROMPT_ROOT / "guards" / "safety" / f"{name}.txt"
    elif role == "planner":
        path = PROMPT_ROOT / "orchestration" / "planner" / f"{name}.txt"
    else:
        path = PROMPT_ROOT / "stages" / stage / f"{name}.txt"

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    return path.read_text(encoding="utf-8")
