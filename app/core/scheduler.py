# app/core/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.generate_weekly_report import generate_weekly_reports


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    scheduler.add_job(
        generate_weekly_reports,
        CronTrigger(day_of_week='mon', hour=0, minute=5, timezone="Asia/Seoul"),
        id="weekly_report_job",
        replace_existing=True
    )

    scheduler.start()
    print("📌 APScheduler started: Weekly Report Job")