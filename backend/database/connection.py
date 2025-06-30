import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1) Pull directly from environment—no load_dotenv() in production
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "🛑 DATABASE_URL environment variable is not set. "
        "Did you wire it up in render.yaml?"
    )

# 2) Create SQLAlchemy engine with pre-ping for reliability
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3) Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 4) Base class for models
Base = declarative_base()

# 5) Dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
