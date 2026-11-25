from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.api.deps import get_current_user
from app.models.all_models import VideoJob, Story, User, Topic
from app.schemas.all_schemas import JobOut
from app.services.pipeline_orchestrator import PipelineOrchestrator

router = APIRouter()

def run_pipeline_background(job_id: int):
    db = SessionLocal()
    try:
        orchestrator = PipelineOrchestrator(db)
        # run_job() marks the job failed + logs the full traceback on any error
        orchestrator.run_job(job_id)
    finally:
        db.close()

@router.get("/", response_model=List[JobOut])
def list_jobs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobs = db.query(VideoJob).order_by(VideoJob.id.desc()).offset(skip).limit(limit).all()
    return jobs

@router.post("/trigger", response_model=JobOut)
def trigger_new_pipeline(
    background_tasks: BackgroundTasks,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orchestrator = PipelineOrchestrator(db)
    
    # Check or create topic
    if topic_id:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
    else:
        topic = orchestrator.story_gen.generate_daily_topic(db)
        
    story = orchestrator.story_gen.generate_full_story(topic, db)
    script = orchestrator.story_gen.generate_scene_script(story, db)

    job = VideoJob(
        story_id=story.id,
        stage="queued",
        progress=0,
        status="in_progress"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_pipeline_background, job.id)
    return job
