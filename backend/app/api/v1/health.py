import os
import shutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/")
def health_check(db: Session = Depends(get_db)):
    # 1. Database check
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_err = str(e)
        
    # 2. Storage check
    storage_path = settings.STORAGE_DIR
    storage_path.mkdir(parents=True, exist_ok=True)
    total, used, free = shutil.disk_usage(storage_path)
    free_gb = round(free / (2**30), 2)
    
    # 3. FFmpeg check
    ffmpeg_available = False
    try:
        import imageio_ffmpeg
        ffmpeg_available = bool(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        ffmpeg_available = shutil.which("ffmpeg") is not None
        
    # 4. Gemini API key configured
    gemini_ready = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "app_env": settings.APP_ENV,
        "database_connected": db_ok,
        "free_disk_space_gb": free_gb,
        "ffmpeg_ready": ffmpeg_available,
        "gemini_api_configured": gemini_ready,
        "tts_voice": settings.TAMIL_TTS_VOICE,
        "auto_publish_enabled": settings.AUTO_PUBLISH_ENABLED,
        "daily_publish_time": settings.DAILY_PUBLISH_TIME,
        "timezone": settings.TIMEZONE
    }
