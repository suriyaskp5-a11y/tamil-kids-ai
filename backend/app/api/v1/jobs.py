from typing import List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.api.deps import get_current_user
from app.core.security import decode_access_token
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


@router.get("/{job_id}/download")
def download_video(
    job_id: int,
    token: str,
    inline: bool = False,
    db: Session = Depends(get_db),
):
    """
    Download (or stream with inline=true) the finished MP4 of a job.
    A plain <a href> can't send an Authorization header, so the JWT comes as ?token=
    """
    username = decode_access_token(token)
    user = db.query(User).filter(User.username == username).first() if username else None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job or not job.video:
        raise HTTPException(status_code=404, detail="Video not generated yet for this job")

    path = job.video.video_path
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video file is missing on the server")

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"tamil_kids_story_job_{job_id}.mp4",
        content_disposition_type="inline" if inline else "attachment",
    )
