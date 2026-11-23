import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Tamil Kids AI Automation"
    SECRET_KEY: str = "default_secret_key_change_in_production_1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    API_V1_STR: str = "/api/v1"
    
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "adminpassword123"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    
    DATABASE_URL: str = "sqlite:///./tamil_kids_ai.db"
    
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    TAMIL_TTS_VOICE: str = "ta-IN-PallaviNeural"
    TTS_RATE: str = "+0%"
    TTS_PITCH: str = "+0Hz"
    
    BLENDER_PATH: str = "blender"
    FFMPEG_PATH: str = ""
    TARGET_VIDEO_DURATION_MINUTES: int = 10
    VIDEO_FPS: int = 24
    VIDEO_WIDTH: int = 1920
    VIDEO_HEIGHT: int = 1080
    
    DAILY_PUBLISH_TIME: str = "09:00"
    TIMEZONE: str = "Asia/Kolkata"
    AUTO_PUBLISH_ENABLED: bool = False
    REQUIRE_MANUAL_APPROVAL: bool = True
    
    YOUTUBE_CLIENT_SECRETS_FILE: str = str(BACKEND_DIR / "client_secrets.json")
    YOUTUBE_OAUTH_TOKEN_FILE: str = str(BACKEND_DIR / "youtube_token.json")
    YOUTUBE_MADE_FOR_KIDS: bool = True
    YOUTUBE_PRIVACY_STATUS: str = "private"
    
    # Path shortcuts
    STORAGE_DIR: Path = ROOT_DIR / "storage"
    TEMP_DIR: Path = ROOT_DIR / "storage" / "temp"
    OUTPUT_DIR: Path = ROOT_DIR / "storage" / "output"
    THUMBNAIL_DIR: Path = ROOT_DIR / "storage" / "thumbnails"
    MEDIA_DIR: Path = ROOT_DIR / "media"
    FONTS_DIR: Path = ROOT_DIR / "media" / "fonts"
    MUSIC_DIR: Path = ROOT_DIR / "media" / "music"
    SFX_DIR: Path = ROOT_DIR / "media" / "sfx"
    BLENDER_DIR: Path = ROOT_DIR / "blender"
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = str(BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
