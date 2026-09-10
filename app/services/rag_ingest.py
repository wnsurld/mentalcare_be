# app/services/rag_ingest.py
# JSONL → PGVector 인덱싱 로직 (서비스 레이어)
import json
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.models.rag_document import RagDocument
from app.db.session import SessionLocal
from pgvector.sqlalchemy import Vector

BLOCK_PATTERNS = [
    "Request unsuccessful. Incapsula incident ID",
    "Access Denied",
    "Error 403",
    "403 Forbidden",
    "To continue, please enable JavaScript",
    "are you a robot",
]


def is_blocked_or_invalid_text(text: str, min_length: int = 300) -> bool:
    if not text:
        return True
    if len(text.strip()) < min_length:
        return True

    lower = text.lower()
    for pattern in BLOCK_PATTERNS:
        if pattern.lower() in lower:
            return True
    return False


def get_embedding(text: str) -> List[float]:
    """
    TODO: 여기에 실제 임베딩 API(Gemini / OpenAI / Vertex 등) 연동
    지금은 placeholder.
    """
    dim = 768
    return [float(len(text) % 10) / 10.0] * dim


def ingest_tagged_docs(jsonl_path: str | Path) -> None:
    jsonl_path = Path(jsonl_path)
    if not jsonl_path.exists():
        raise FileNotFoundError(f"File not found: {jsonl_path}")

    session: Session = SessionLocal()
    inserted = 0
    skipped_blocked = 0
    skipped_error = 0

    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    skipped_error += 1
                    continue

                doc_id = rec.get("doc_id")
                source_url = rec.get("source_url")
                doc_type = rec.get("doc_type")
                text = rec.get("text") or ""
                emotions = rec.get("emotions") or []
                situations = rec.get("situations") or []

                if is_blocked_or_invalid_text(text):
                    skipped_blocked += 1
                    continue

                embedding = get_embedding(text)

                existing = (
                    session.query(RagDocument)
                    .filter(RagDocument.doc_id == doc_id)
                    .one_or_none()
                )

                if existing:
                    existing.source_url = source_url
                    existing.doc_type = doc_type
                    existing.text = text
                    existing.emotions = emotions
                    existing.situations = situations
                    existing.embedding = embedding
                else:
                    doc = RagDocument(
                        doc_id=doc_id,
                        source_url=source_url,
                        doc_type=doc_type,
                        text=text,
                        emotions=emotions,
                        situations=situations,
                        embedding=embedding,
                    )
                    session.add(doc)

                inserted += 1
                if inserted % 50 == 0:
                    session.commit()

        session.commit()
        print(
            f"[RAG ingest] inserted/updated={inserted}, "
            f"blocked_or_too_short={skipped_blocked}, json_error={skipped_error}"
        )
    finally:
        session.close()
