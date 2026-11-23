from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.all_models import Topic, Story, VideoJob, GeneratedVideo, YouTubeUpload, User
from app.schemas.all_schemas import DashboardSummary, JobOut
from app.core.config import settings

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_topics = db.query(Topic).count()
    total_stories = db.query(Story).count()
    total_jobs = db.query(VideoJob).count()
    published_videos = db.query(YouTubeUpload).filter(YouTubeUpload.upload_status == "uploaded").count()
    failed_jobs = db.query(VideoJob).filter(VideoJob.status == "failed").count()
    
    active_job = db.query(VideoJob).filter(VideoJob.status == "in_progress").order_by(VideoJob.id.desc()).first()

    return DashboardSummary(
        total_topics=total_topics,
        total_stories=total_stories,
        total_jobs=total_jobs,
        published_videos=published_videos,
        failed_jobs=failed_jobs,
        next_scheduled_run=f"{settings.DAILY_PUBLISH_TIME} {settings.TIMEZONE}",
        auto_publish_enabled=settings.AUTO_PUBLISH_ENABLED,
        require_manual_approval=settings.REQUIRE_MANUAL_APPROVAL,
        current_active_job=JobOut.from_orm(active_job) if active_job else None
    )
