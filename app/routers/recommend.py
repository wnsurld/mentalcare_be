# app/routers/recommend.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.recommend import (
    RoutineRecommendRequest,
    RoutineRecommendResponse,
    RoutineRecommendItem,
)
from app.services.recommend_service import recommend_routines_by_text


router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.post(
    "/routines",
    response_model=RoutineRecommendResponse,
    status_code=status.HTTP_200_OK,
)
def recommend_routines(
    payload: RoutineRecommendRequest,
    db: Session = Depends(get_db),
):
    try:
        results = recommend_routines_by_text(
            db=db,
            text=payload.text,
            limit=payload.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RoutineRecommendResponse(
        routines=[
            RoutineRecommendItem(
                routine_id=r.routine_id,
                title=r.title,
                description=r.description,
                score=r.score,
            )
            for r in results
        ]
    )
