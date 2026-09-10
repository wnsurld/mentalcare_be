# app/services/weekly_report_service.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.reports import SessionReport, WeeklyReport
from app.models.chat_session import ChatSession
import json, os
from app.core.prompt_loader import load_prompt
from google import genai
from google.genai import types


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_weekly_reports():
    db: Session = SessionLocal()

    try:
        # 한국시간 now
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))

        # 지난주 월요일 00:00
        last_monday_kst = (now_kst - timedelta(days=now_kst.weekday()+7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # 지난주 일요일 23:59:59
        last_sunday_kst = last_monday_kst + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # DB created_at은 UTC이므로 비교를 위해 UTC로 변환
        last_monday_utc = last_monday_kst.astimezone(ZoneInfo("UTC"))
        last_sunday_utc = last_sunday_kst.astimezone(ZoneInfo("UTC"))

        
        week_number = get_month_week(last_monday_kst.date())   # 몇 주차인지 계산
        year = last_monday_kst.date().year
        month = last_monday_kst.date().month
        week_info = f"{year}년 {month}월 {week_number}주차"
        print(f"🔍 주간 리포트 대상 기간: {last_monday_kst} ~ {last_sunday_kst} // {week_info}")

        # session_report 존재하는 user_id 목록 조회
        user_ids = (
            db.query(ChatSession.user_id)
            .join(SessionReport, SessionReport.session_id == ChatSession.id)
            .filter(SessionReport.created_at >= last_monday_utc)
            .filter(SessionReport.created_at <= last_sunday_utc)
            .distinct()
            .all()
        )

        if not user_ids:
            print("⚠️ 이 기간에 session_report가 있는 유저가 없음.")
            return

        print(f"📌 이번 주 처리할 유저 수: {len(user_ids)} 명")

        # 유저별 처리
        for (user_id,) in user_ids:
            print(f"➡ 유저 {user_id} 처리중...")

            # 유저별 session_report 조회
            reports = (
                db.query(SessionReport)
                .join(SessionReport.session)
                .filter(ChatSession.user_id == user_id)
                .filter(SessionReport.created_at >= last_monday_utc)   
                .filter(SessionReport.created_at <= last_sunday_utc)
                .order_by(SessionReport.created_at)
                .all()
            )

            # LLM 입력 데이터 조립
            llm_input = [{
                "mood_overview": r.mood_overview,
                "created_at": r.created_at.astimezone(ZoneInfo("Asia/Seoul")).isoformat(), 
                "highlights": r.highlights,
            } for r in reports]

            
            routine_overviews = [r.routine_overview for r in reports]


            # 3) LLM 호출
            llm_output = generate_weekly_llm_report(llm_input)

            # 4) DB 저장 => weekly reports db 수정하기
            weekly = WeeklyReport(
                user_id = user_id,
                week_info = week_info,
                week_start_date=last_monday_kst.date(),
                mood_distribution = llm_output["mood_distribution"],
                weekly_mood_analysis = llm_output["weekly_mood_analysis"],
                mood_manage_tip = llm_output["mood_manage_tip"],
                positive_highlights = llm_output["positive_highlights"],
                routine_overview = routine_overviews
            )

            db.add(weekly)
            db.commit()

            print(f"✅ 유저 {user_id} 주간 리포트 생성 완료!")

        print("🎉 모든 유저 주간 리포트 생성 완료!")

    except Exception as e:
        db.rollback()
        print("❌ 주간 리포트 생성 오류:", e)

    finally:
        db.close()


def get_month_week(date):

    first_day = date.replace(day=1)
    start_weekday = first_day.weekday()  
    day_number = date.day
    week = ((start_weekday + day_number - 1) // 7) + 1

    return week


def generate_weekly_llm_report(input_list):
    """
    input_list 예시:
    [
      {"mood_overview": "...", "created_at": "2025-11-17T09:30:00+09:00", "highlights": "..."},
      {"mood_overview": "...", "created_at": "2025-11-18T22:10:00+09:00", "highlights": "..."}
    ]
    """
    
    llm_input = json.dumps(input_list, ensure_ascii=False, indent=2)
    
    system_prompt = load_prompt(
        stage="report",
        name="generate_weekly_report"
    )

    emotion_detail_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "emotion": types.Schema(
                type=types.Type.STRING,
                description="분석 후 통합된 감정 이름"
            ),
            "value": types.Schema(
                type=types.Type.STRING,
                description="해당 감정이 차지하는 비율"
            )
        },
        required=["emotion", "value"]
    )

    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "mood_distribution": types.Schema(
                type=types.Type.ARRAY,
                description="분석된 모든 감정과 그 비율을 객체 리스트 형태로 담습니다.",
                items=emotion_detail_schema 
            ),
            "weekly_mood_analysis": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "dawn": types.Schema(type=types.Type.STRING, description="새벽(00-07시) 감정 패턴 분석"),
                    "morning": types.Schema(type=types.Type.STRING, description="오전(07-12시) 감정 패턴 분석"),
                    "afternoon": types.Schema(type=types.Type.STRING, description="오후(12-18시) 감정 패턴 분석"),
                    "evening": types.Schema(type=types.Type.STRING, description="저녁(18-00시) 감정 패턴 분석")
                },
                required=["dawn", "morning", "afternoon", "evening"]
            ),
            "mood_manage_tip": types.Schema(
                type=types.Type.STRING, 
                description="weekly_mood_analysis을 기반으로 한 맞춤형 감정 관리 팁."
            ),
            "positive_highlights": types.Schema(
                type=types.Type.STRING, 
                description="긍정적인 사건 요약."
            )
        },
        required=["mood_distribution", "weekly_mood_analysis", "mood_manage_tip", "positive_highlights"]
    )
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=response_schema       
    )

    response = client.models.generate_content(
        model = "gemini-2.5-pro",
        contents = [
            types.Content(
                role = "user",
                parts = [types.Part.from_text(text=llm_input)]
            )
        ],
        config=config 
    )
    result = response.text
    print(f"llm함수: {result}")
    return json.loads(result)


def modify_llm(user_msg, stage, name):

    system_prompt = load_prompt(
        stage=stage,
        name=name
    )

    config = types.GenerateContentConfig(system_instruction=system_prompt)

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            types.Content(role="user", parts=[types.Part.from_text(text=user_msg)])
        ],
        config=config
    )

    result = response.text
    return result