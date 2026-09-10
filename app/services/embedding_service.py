# app/services/embedding_service.py
# retrive를 위한 임베딩 생성 서비스
import google.generativeai as genai
import os
from functools import lru_cache

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


@lru_cache
def _configure():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=GEMINI_API_KEY)
    return True


def get_embedding(text: str) -> list[float]:
    _configure()

    text = text[:3000]  # 너무 길면 잘라주기
    resp = genai.embed_content(
        model="text-embedding-004",  # 768차원 출력
        content=text,
    )
    return resp["embedding"]
