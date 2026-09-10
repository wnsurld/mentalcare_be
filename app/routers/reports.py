from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.reports import SessionReport, WeeklyReport
from app.models.chat_session import ChatSession
from app.schemas.reports import SessionReportList, WeeklyReportList, SessionReportDetail, WeeklyReportDetail
from app.services.chat_service import can_create_session_report

router = APIRouter(prefix="/api/reports", tags=["reports"])

#리포트 목록 조회
@router.get("/sessionReports", response_model=List[SessionReportList])
def get_session_list(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    #세션 리포트 목록
    session_reports = (                                 
        db.query(SessionReport)
        .join(SessionReport.session)
        .filter(ChatSession.user_id == user.id)
        .order_by(SessionReport.created_at.desc())
        .all()
    )

    return session_reports    #일단 report_id와 created_at만 반환, 추후 목록에 보여줄 내용 정해야함
                               
@router.get("/weeklyReports", response_model=List[WeeklyReportList])
def get_week_list(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    #주간 리포트 목록
    weekly_reports = (
        db.query(WeeklyReport)
        .filter(WeeklyReport.user_id == user.id)
        .order_by(WeeklyReport.week_start_date.desc())
        .all()
    )

    return weekly_reports 





#세션 리포트 상세 조회
@router.get("/sessionReports/{report_id}", response_model=SessionReportDetail)
def get_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    session_report = (
        db.query(SessionReport)
        .join(SessionReport.session)
        .filter(
            SessionReport.report_id == report_id,
            ChatSession.user_id == user.id
        )
        .first()
    )

    if not session_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return session_report


#주간 리포트 상세 조회
@router.get("/weeklyReports/{weekly_id}", response_model=WeeklyReportDetail)
def get_weekly_detail(
    weekly_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    weekly_report = (
        db.query(WeeklyReport)
        .filter(
            WeeklyReport.weekly_id == weekly_id,
            WeeklyReport.user_id == user.id
        )
        .first()
    )

    if not weekly_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return weekly_report
