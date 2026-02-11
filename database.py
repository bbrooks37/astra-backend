import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Fetch the URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Fix the Render 'postgres://' vs SQLAlchemy 'postgresql://' issue
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Fallback for local development if DATABASE_URL is missing
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./local.db"
    print("⚠️ DATABASE_URL not found, falling back to local SQLite.")

# 4. Create the SQLAlchemy engine
# Added 'pool_recycle' to prevent connection timeouts on Render
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_recycle=300
)

# 5. Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()