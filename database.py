import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load variables from .env into the system environment
load_dotenv()

# Fetch the URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file. Please check your configuration.")

# Create the SQLAlchemy engine
# pool_pre_ping checks if the connection is alive before using it
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models to inherit from
Base = declarative_base()

# Dependency for FastAPI to handle opening/closing DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()