import asyncio
from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "parabench",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Tunis",
    enable_utc=True,
    beat_schedule={
        "daily-scraping": {
            "task": "services.celery_app.run_daily_scraping",
            "schedule": crontab(
                hour=int(os.getenv("SCRAPING_CRON_HOUR", 2)),
                minute=int(os.getenv("SCRAPING_CRON_MINUTE", 0))
            ),
        },
    },
)


@celery_app.task(name="services.celery_app.run_daily_scraping")
def run_daily_scraping():
    from models.database import SessionLocal
    from services.scraping_service import run_scraping_job, create_scraping_job
    
    db = SessionLocal()
    try:
        sites = ["parashop", "parafendri", "tunisiepara"]
        job_id = create_scraping_job(db, sites)
        asyncio.run(run_scraping_job(db, sites, job_id))
    finally:
        db.close()


@celery_app.task(name="services.celery_app.run_scraping_task")
def run_scraping_task(job_id: str, sites: list):
    from models.database import SessionLocal
    from services.scraping_service import run_scraping_job
    
    db = SessionLocal()
    try:
        asyncio.run(run_scraping_job(db, sites, job_id))
    finally:
        db.close()
