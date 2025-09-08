"""
Database configuration and connection management
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import logging
from dotenv import load_dotenv

from core.logging import get_logger
from .models import Base

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

logger = get_logger(__name__)

# Database configuration from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # Default for local development
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Validate required environment variables
if not POSTGRES_USER:
    raise ValueError("POSTGRES_USER environment variable is required")
if not POSTGRES_PASSWORD:
    raise ValueError("POSTGRES_PASSWORD environment variable is required")
if not POSTGRES_DB:
    raise ValueError("POSTGRES_DB environment variable is required")

# Create database URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=False           # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """
    Create all database tables
    This should be called during application startup
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


def drop_tables():
    """
    Drop all database tables
    WARNING: This will delete all data!
    """
    try:
        logger.warning("⚠️ Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Database tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Error dropping database tables: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    Use this in FastAPI endpoints with Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for direct use
    Remember to close the session when done
    """
    return SessionLocal()


def test_connection() -> bool:
    """
    Test database connection
    Returns True if connection is successful, False otherwise
    """
    try:
        db = SessionLocal()
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


def init_database():
    """
    Initialize database - create tables and test connection
    Call this during application startup
    """
    logger.info("🗄️ Initializing database...")
    
    # Test connection first
    if not test_connection():
        raise Exception("Database connection failed")
    
    # Create tables
    create_tables()
    
    logger.info("✅ Database initialization completed")


if __name__ == "__main__":
    # For testing purposes
    print("Testing database connection...")
    print(f"Database URL: {DATABASE_URL}")
    
    if test_connection():
        print("✅ Connection successful")
        init_database()
    else:
        print("❌ Connection failed")
