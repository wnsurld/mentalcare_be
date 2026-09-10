# scripts/insert_dummy_weekly_report.py 같은 파일로 만들어도 됨

from datetime import date
from app.db.session import SessionLocal
from app.models.reports import WeeklyReport

def main():
    db = SessionLocal()
    try:
        user_id = "ac3ea90e-d686-4659-becc-5aaaca2ea5f6"  # 실제 users.id 로 교체

        weekly = WeeklyReport(
            user_id=user_id,
            week_start_date=date(2025, 11, 17),
            week_info="2025년 11월 3주차",
            mood_distribution=[
                {"emotion": "불안", "value": "40"},
                {"emotion": "피로", "value": "30"},
                {"emotion": "안정", "value": "20"},
                {"emotion": "기쁨", "value": "10"},
            ],
            weekly_mood_analysis={
                "dawn": "새벽에는 불안과 걱정이 커져 수면이 자주 깼습니다.",
                "morning": "오전에는 출근 준비와 업무 시작으로 긴장감이 높았습니다.",
                "afternoon": "오후에는 업무에 적응하면서 집중과 피로가 번갈아 나타났습니다.",
                "evening": "저녁에는 야근과 업무 반추로 피로와 무기력이 쌓였습니다.",
            },
            mood_manage_tip="주요 불안 시간대를 기준으로 루틴을 배치하면 감정 기복을 줄이는 데 도움이 됩니다.",
            positive_highlights="루틴을 실천한 날에는 스스로를 돌보고 있다는 안도감과 작은 성취감이 느껴졌습니다.",
            routine_overview=[
                {
                    "routine_id": "routine_1",
                    "title": "퇴근 후 긴장 풀기 루틴",
                    "description": "집에 도착하면 10분간 스트레칭 후 따뜻한 샤워를 하며 몸의 긴장을 풀고, 짧은 호흡 명상을 진행합니다.",
                    "frequency": "주 4~5회",
                    "related_mood": "불안 완화",
                },
                {
                    "routine_id": "routine_2",
                    "title": "잠들기 전 디지털 디톡스",
                    "description": "잠들기 30분 전 휴대폰과 노트북 전원을 끄고, 조용한 음악을 들으며 오늘 고마웠던 일을 3가지 적어봅니다.",
                    "frequency": "매일",
                    "related_mood": "수면의 질 개선",
                },
            ],
        )

        db.add(weekly)
        db.commit()
        db.refresh(weekly)
        print("생성된 weekly_id:", weekly.weekly_id)

    finally:
        db.close()

if __name__ == "__main__":
    main()
