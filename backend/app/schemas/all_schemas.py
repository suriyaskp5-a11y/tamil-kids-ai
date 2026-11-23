from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

# Auth & User
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Topic
class TopicCreate(BaseModel):
    title_tamil: str
    title_english: str
    category: str
    target_moral: str
    synopsis: Optional[str] = None

class TopicOut(BaseModel):
    id: int
    title_tamil: str
    title_english: str
    category: str
    target_moral: str
    synopsis: Optional[str] = None
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# Story
class StoryCreate(BaseModel):
    topic_id: int
    title_tamil: str
    moral_tamil: str
    full_story_tamil: str
    character_bible: Optional[List[Dict[str, Any]]] = None
    target_duration_seconds: int = 600

class StoryOut(BaseModel):
    id: int
    topic_id: int
    title_tamil: str
    moral_tamil: str
    full_story_tamil: str
    character_bible: Optional[List[Dict[str, Any]]] = None
    word_count: int
    target_duration_seconds: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# Scene & Script
class SceneItem(BaseModel):
    scene_number: int
    duration_seconds: int
    location: str
    camera_movement: str  # e.g., "Slow zoom into child sitting under banyan tree"
    characters_present: List[str]
    actions: str
    expressions: str
    narration_tamil: str
    dialogue_tamil: Optional[str] = ""
    sfx_cue: Optional[str] = "birds_chirping"
    lighting_mood: Optional[str] = "bright_sunny"

class ScriptOut(BaseModel):
    id: int
    story_id: int
    scene_count: int
    scenes: List[Dict[str, Any]]
    shot_list: Optional[Dict[str, Any]] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Video Job
class JobOut(BaseModel):
    id: int
    story_id: int
    stage: str
    progress: int
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Dashboard Stats Summary
class DashboardSummary(BaseModel):
    total_topics: int
    total_stories: int
    total_jobs: int
    published_videos: int
    failed_jobs: int
    next_scheduled_run: str
    auto_publish_enabled: bool
    require_manual_approval: bool
    current_active_job: Optional[JobOut] = None

# Settings
class SettingUpdate(BaseModel):
    key: str
    value: str
