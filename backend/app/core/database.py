from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


def _normalize_db_url(url: str) -> str:
    """Render/Neon/Supabase give 'postgres://' but SQLAlchemy 2 needs 'postgresql://'."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = _normalize_db_url(settings.DATABASE_URL)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# For SQLite, enable check_same_thread=False
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

engine_kwargs = {"connect_args": connect_args, "pool_pre_ping": True}
if not IS_SQLITE:
    # Keep connections small + recycled (free Postgres plans have low limits)
    engine_kwargs.update({"pool_size": 3, "max_overflow": 2, "pool_recycle": 300})

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
