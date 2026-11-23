import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger("TamilKidsAI.Scheduler")

scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)

def daily_pipeline_task():
    logger.info("Triggering scheduled daily Tamil kids video automation...")
    db = SessionLocal()
    try:
        orchestrator = PipelineOrchestrator(db)
        orchestrator.run_daily_pipeline()
    except Exception as e:
        logger.error(f"Scheduled pipeline run encountered an error: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        hour, minute = settings.DAILY_PUBLISH_TIME.split(":")
        trigger = CronTrigger(
            hour=int(hour),
            minute=int(minute),
            timezone=settings.TIMEZONE
        )
        scheduler.add_job(
            daily_pipeline_task,
            trigger=trigger,
            id="daily_tamil_kids_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Daily scheduler started. Next run at {settings.DAILY_PUBLISH_TIME} {settings.TIMEZONE}")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully.")
