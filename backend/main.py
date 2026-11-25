import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.all_models import User
from app.api.v1 import auth, health, dashboard, topics, stories, jobs, settings as settings_api
from app.scheduler.daily_scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TamilKidsAI")

# Database table initialization & default admin seeding
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                email="admin@tamilkids.ai",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_admin=True,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Default admin user created: {settings.ADMIN_USERNAME}")
        # Jobs left "in_progress" by a crash/restart can never finish - mark them failed
        from app.models.all_models import VideoJob
        stuck = db.query(VideoJob).filter(VideoJob.status == "in_progress").all()
        for j in stuck:
            j.status = "failed"
            j.error_message = f"Interrupted at stage '{j.stage}' (server restarted). Trigger a new job."
        if stuck:
            db.commit()
            logger.warning(f"Marked {len(stuck)} interrupted job(s) as failed")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Tamil Kids AI backend services...")
    init_db()
    
    # Ensure storage paths exist
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start scheduler
    try:
        start_scheduler()
    except Exception as e:
        logger.warning(f"Could not start scheduler on startup: {e}")
        
    yield
    
    # Shutdown
    logger.info("Shutting down Tamil Kids AI backend services...")
    stop_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated YouTube Kids 3D Animation & Tamil Storytelling Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts for previews (videos, thumbnails)
app.mount("/storage/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output_videos")
app.mount("/storage/thumbnails", StaticFiles(directory=str(settings.THUMBNAIL_DIR)), name="thumbnails")

# Router inclusions
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["System Health"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard"])
app.include_router(topics.router, prefix=f"{settings.API_V1_STR}/topics", tags=["Topics"])
app.include_router(stories.router, prefix=f"{settings.API_V1_STR}/stories", tags=["Stories"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Video Jobs"])
app.include_router(settings_api.router, prefix=f"{settings.API_V1_STR}/settings", tags=["Settings"])

@app.get("/")
def root():
    return {
        "message": "Tamil Kids AI Automation API is running.",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
