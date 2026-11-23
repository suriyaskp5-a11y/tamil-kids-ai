from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.all_models import Topic, User
from app.schemas.all_schemas import TopicOut
from app.services.ai_story_generator import AIStoryGeneratorService

router = APIRouter()

@router.get("/", response_model=List[TopicOut])
def list_topics(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    topics = db.query(Topic).order_by(Topic.id.desc()).offset(skip).limit(limit).all()
    return topics

@router.post("/generate", response_model=TopicOut)
def generate_topic(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AIStoryGeneratorService()
    topic = service.generate_daily_topic(db)
    return topic
