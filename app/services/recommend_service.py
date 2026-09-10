# app/services/recommend_service.py
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.routine import Routine
from app.services.embedding_service import get_embedding


class RoutineRecommendItemDTO:
    def __init__(self, routine_id: str, title: str, description: str, score: float):
        self.routine_id = routine_id
        self.title = title
        self.description = description
        self.score = score


def recommend_routines_by_text(
    db: Session,
    text: str,
    limit: int = 5,
) -> List[RoutineRecommendItemDTO]:

    query_embedding = get_embedding(text)

    distance_expr = Routine.embedding.cosine_distance(query_embedding)

    stmt = (
        select(Routine, distance_expr.label("distance"))
        .where(Routine.embedding != None)
        .order_by(distance_expr.asc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    results = []
    for routine, distance in rows:
        score = max(0.0, 1.0 - float(distance))
        results.append(
            RoutineRecommendItemDTO(
                routine_id=routine.routine_id,
                title=routine.title,
                description=routine.description or "",
                score=score,
            )
        )

    return results
