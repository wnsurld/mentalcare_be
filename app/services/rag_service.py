# app/services/rag_service.py

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text, bindparam, Integer
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

from app.services.embedding_service import get_embedding

EMBED_DIM = 768

# 코사인 거리 기준 검색을 가정
DISTANCE_OPERATOR = "<=>"
MAX_DISTANCE: float | None = None  # 예: 0.7 같은 threshold 주고 싶으면 값 넣기

logger = logging.getLogger(__name__)


def retrieve(query: str, db: Session, top_k: int = 5) -> Dict[str, Any]:
    query_vec = get_embedding(query)  # List[float], len=EMBED_DIM

    if not query_vec:
        return {"docs": []}

    sql = f"""
        SELECT
            routine_id,
            title,
            description,
            steps,
            target_emotions,
            target_situations,
            tags,
            embedding {DISTANCE_OPERATOR} :q AS distance
        FROM routines
        WHERE embedding IS NOT NULL
        ORDER BY embedding {DISTANCE_OPERATOR} :q
        LIMIT :k
    """

    stmt = text(sql).bindparams(
        bindparam("q", value=query_vec, type_=Vector(EMBED_DIM)),
        bindparam("k", value=top_k, type_=Integer),
    )

    rows = db.execute(stmt).mappings().all()

    if not rows:
        return {"docs": []}

    docs: List[Dict[str, Any]] = []
    for row in rows:
        dist = float(row["distance"])

        if MAX_DISTANCE is not None and dist > MAX_DISTANCE:
            continue

        docs.append(
            {
                "routine_id": row["routine_id"],
                "title": row["title"],
                "description": row["description"],
                "steps": row["steps"],
                "target_emotions": row["target_emotions"],
                "target_situations": row["target_situations"],
                "tags": row["tags"],
                "distance": dist,
            }
        )

    logger.info(
        "[RAG][retrieve] query=%r | top=%r",
        query[:80],
        [(d["routine_id"], d["title"], round(d["distance"], 4)) for d in docs],
    )

    return {"docs": docs}


def aggregate(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    (현재는 사용하지 않지만, 나중에 '여러 루틴 합쳐서 하나의 long draft'가 필요하면
    다시 사용할 수 있게 남겨두는 함수)
    """
    if not docs:
        return {"routine_draft": "", "source_docs": []}

    lines: List[str] = []
    for i, d in enumerate(docs, start=1):
        line = f"{i}. {d['title']}\n"
        if d.get("description"):
            line += f"- 설명: {d['description']}\n"
        if d.get("steps"):
            line += "- 단계:\n"
            for idx, step in enumerate(d["steps"], start=1):
                line += f"  {idx}) {step}\n"
        if d.get("target_emotions"):
            line += f"- 대상 감정: {', '.join(d['target_emotions'])}\n"
        if d.get("target_situations"):
            line += f"- 대상 상황: {', '.join(d['target_situations'])}\n"
        if d.get("tags"):
            line += f"- 태그: {', '.join(d['tags'])}\n"
        line += "\n"
        lines.append(line)

    routine_draft = "".join(lines)

    return {
        "routine_draft": routine_draft,
        "source_docs": docs,
    }


def run_rag_pipeline(
    query: str,
    db: Session,
    top_k: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    고수준 RAG 파이프라인:

      1) query로 retrieve 호출
      2) docs만 그대로 반환 (문자열 draft는 더 이상 만들지 않는다)

    성공 시:
      {
        "source_docs": [ {routine 후보들...} ]
      }
    실패 시:
      None
    """
    retrieved = retrieve(query, db, top_k=top_k)
    docs = retrieved.get("docs") or []
    if not docs:
        return None

    # 이제 aggregate는 사용하지 않고, 후보들만 넘긴다.
    return {"source_docs": docs}
