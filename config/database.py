from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.settings import settings
from utils.logger import logger
import os

Base = declarative_base()

def get_database_url():
    """Get database URL based on configuration"""
    if settings.DB_TYPE.lower() == "sqlite":
        logger.info("Using SQLite database")
        return settings.SQLITE_URL
    
    try:
        return (
            f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
    except Exception as e:
        logger.warning(f"MySQL configuration failed: {str(e)}, falling back to SQLite")
        return settings.SQLITE_URL

def create_db_engine():
    """Create database engine with proper configuration"""
    db_url = get_database_url()
    connect_args = {}
    
    if db_url.startswith('sqlite'):
        connect_args["check_same_thread"] = False
    
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args
        )
        return engine
    except Exception as e:
        logger.error(f"Failed to create engine: {str(e)}")
        if not db_url.startswith("sqlite"):
            logger.info("Falling back to SQLite database")
            return create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
    return None

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Synchronous database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        if db is not None:
            db.close()

def get_async_db():
    """Async database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        if db is not None:
            db.close()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
