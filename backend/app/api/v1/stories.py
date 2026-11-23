from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.all_models import Story, Topic, User
from app.schemas.all_schemas import StoryOut
from app.services.ai_story_generator import AIStoryGeneratorService

router = APIRouter()

@router.get("/", response_model=List[StoryOut])
def list_stories(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stories = db.query(Story).order_by(Story.id.desc()).offset(skip).limit(limit).all()
    return stories

@router.post("/generate/{topic_id}", response_model=StoryOut)
def generate_story_for_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    service = AIStoryGeneratorService()
    story = service.generate_full_story(topic, db)
    # Also generate structured script
    service.generate_scene_script(story, db)
    return story
