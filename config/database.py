from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.settings import settings
from utils.logger import logger

# Construct database URL
DATABASE_URL = (
    f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

logger.info(f"Using database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

# Create engine without SSL for local development
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "use_pure": True,  # Use pure Python implementation
        "auth_plugin": 'mysql_native_password'  # Use native password auth
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
