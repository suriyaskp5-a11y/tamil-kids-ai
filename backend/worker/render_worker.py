"""
Standalone Render Worker CLI
Can run continuously on a local PC (using local GPU for high-speed Blender rendering)
or on a cloud instance.
"""

import time
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.all_models import VideoJob
from app.services.pipeline_orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Worker] %(message)s")
logger = logging.getLogger("TamilKidsAI.Worker")

def run_worker_loop():
    logger.info("Tamil Kids AI Render Worker started. Polling for queued jobs...")
    while True:
        db = SessionLocal()
        try:
            # Query oldest pending/queued job
            # API creates jobs as status="in_progress", stage="queued"; accept both styles
            job = (
                db.query(VideoJob)
                .filter(VideoJob.stage == "queued", VideoJob.status.in_(["queued", "in_progress"]))
                .order_by(VideoJob.id.asc())
                .first()
            )
            if job:
                logger.info(f"Picked up job #{job.id} for story #{job.story_id}")
                PipelineOrchestrator(db).run_job(job.id)
            else:
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Worker encountered error: {e}")
            time.sleep(5)
        finally:
            db.close()

if __name__ == "__main__":
    run_worker_loop()
