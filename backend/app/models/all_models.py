from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    title_tamil = Column(String(255), index=True, nullable=False)
    title_english = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False)  # animal, friendship, honesty, nature, etc.
    target_moral = Column(String(255), nullable=False)
    synopsis = Column(Text, nullable=True)
    status = Column(String(50), default="proposed", index=True)  # proposed, approved, used, rejected
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    stories = relationship("Story", back_populates="topic")

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title_tamil = Column(String(255), nullable=False)
    moral_tamil = Column(String(255), nullable=False)
    full_story_tamil = Column(Text, nullable=False)
    character_bible = Column(JSON, nullable=True)  # List of characters with names, visual details
    word_count = Column(Integer, default=0)
    target_duration_seconds = Column(Integer, default=600)  # ~10 min
    status = Column(String(50), default="draft")  # draft, approved, scripted, completed
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    topic = relationship("Topic", back_populates="stories")
    script = relationship("Script", back_populates="story", uselist=False)
    jobs = relationship("VideoJob", back_populates="story")

class Script(Base):
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    scene_count = Column(Integer, default=0)
    scenes = Column(JSON, nullable=False)  # List of structured scene objects
    shot_list = Column(JSON, nullable=True)  # Blender camera angles & asset requirements
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    story = relationship("Story", back_populates="script")

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name_tamil = Column(String(100), nullable=False)
    name_english = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    blend_file_path = Column(String(255), nullable=True)
    rig_type = Column(String(100), default="rigify")
    thumbnail_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class MediaAsset(Base):
    __tablename__ = "media_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)  # music, sfx, font, 3d_model, environment
    file_path = Column(String(255), nullable=False)
    duration_seconds = Column(Float, nullable=True)
    license_type = Column(String(100), default="CC0 / Public Domain")
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class VideoJob(Base):
    __tablename__ = "video_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    stage = Column(String(50), default="pending", index=True) 
    # Stages: pending, tts_generating, scenes_rendering, assembling, thumbnailing, validating, ready_to_upload, uploading, completed, failed
    progress = Column(Integer, default=0)  # 0 to 100
    status = Column(String(50), default="queued")  # queued, in_progress, paused, completed, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    story = relationship("Story", back_populates="jobs")
    video = relationship("GeneratedVideo", back_populates="job", uselist=False)
    logs = relationship("ErrorLog", back_populates="job")

    @property
    def video_ready(self) -> bool:
        return self.video is not None and bool(self.video.video_path)

class GeneratedVideo(Base):
    __tablename__ = "generated_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("video_jobs.id"), nullable=False)
    video_path = Column(String(255), nullable=False)
    thumbnail_path = Column(String(255), nullable=True)
    srt_path = Column(String(255), nullable=True)
    audio_path = Column(String(255), nullable=True)
    duration_seconds = Column(Float, nullable=False)
    resolution = Column(String(20), default="1920x1080")
    fps = Column(Integer, default=24)
    file_size_mb = Column(Float, nullable=True)
    is_validated = Column(Boolean, default=False)
    validation_report = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    job = relationship("VideoJob", back_populates="video")
    upload = relationship("YouTubeUpload", back_populates="video", uselist=False)

class YouTubeUpload(Base):
    __tablename__ = "youtube_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("generated_videos.id"), nullable=False)
    youtube_video_id = Column(String(100), unique=True, index=True, nullable=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    privacy_status = Column(String(50), default="private")  # private, unlisted, public
    made_for_kids = Column(Boolean, default=True)
    publish_at = Column(DateTime(timezone=True), nullable=True)
    upload_status = Column(String(50), default="pending")  # pending, uploaded, scheduled, failed
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    
    video = relationship("GeneratedVideo", back_populates="upload")

class AutomationSetting(Base):
    __tablename__ = "automation_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class ErrorLog(Base):
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("video_jobs.id"), nullable=True)
    level = Column(String(20), default="ERROR")  # INFO, WARNING, ERROR, CRITICAL
    stage = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    job = relationship("VideoJob", back_populates="logs")
