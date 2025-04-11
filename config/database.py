from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.logger import logger
from config.settings import settings
import os

def get_database_url():
    """Get database URL with fallbacks"""
    # First try Railway's URL
    if "MYSQL_URL" in os.environ:
        url = os.environ["MYSQL_URL"]
        # Remove ssl-mode from URL
        if "ssl-mode" in url:
            url = url.split("?")[0]
        return url.replace('mysql://', 'mysql+mysqlconnector://')
    
    # Fallback to constructed URL
    return f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Get Database URL
DATABASE_URL = get_database_url()
logger.info(f"Using database: {DATABASE_URL.split('@')[1]}")  # Log without credentials

# Create engine without SSL settings
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

def init_db():
    import models.users  # Import models to register them
    import models.logs
    
    try:
        # Only create tables that don't exist
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables verified/created successfully")
        
        # Check if users table needs LONGBLOB modification
        with engine.connect() as conn:
            # Check column type
            result = conn.execute(text("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'image'
            """))
            column_type = result.scalar()
            
            # Only modify if not already LONGBLOB and table exists
            if column_type and 'longblob' not in column_type.lower():
                conn.execute(text("ALTER TABLE users MODIFY COLUMN image LONGBLOB"))
                logger.info("Updated users.image column to LONGBLOB")
            conn.commit()
            
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise
