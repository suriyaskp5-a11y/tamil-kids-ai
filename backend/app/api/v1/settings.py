from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.all_models import AutomationSetting, User
from app.schemas.all_schemas import SettingUpdate
from app.core.config import settings

router = APIRouter()

@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    db_settings = db.query(AutomationSetting).all()
    settings_dict = {s.key: s.value for s in db_settings}
    
    # Defaults from config
    return {
        "auto_publish_enabled": settings_dict.get("auto_publish_enabled", str(settings.AUTO_PUBLISH_ENABLED).lower()),
        "require_manual_approval": settings_dict.get("require_manual_approval", str(settings.REQUIRE_MANUAL_APPROVAL).lower()),
        "daily_publish_time": settings_dict.get("daily_publish_time", settings.DAILY_PUBLISH_TIME),
        "timezone": settings_dict.get("timezone", settings.TIMEZONE),
        "target_duration_minutes": settings_dict.get("target_duration_minutes", str(settings.TARGET_VIDEO_DURATION_MINUTES)),
        "tamil_tts_voice": settings_dict.get("tamil_tts_voice", settings.TAMIL_TTS_VOICE),
        "youtube_privacy_status": settings_dict.get("youtube_privacy_status", settings.YOUTUBE_PRIVACY_STATUS)
    }

@router.put("/")
def update_setting(
    payload: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = db.query(AutomationSetting).filter(AutomationSetting.key == payload.key).first()
    if not setting:
        setting = AutomationSetting(key=payload.key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.commit()
    return {"status": "success", "key": payload.key, "value": payload.value}
