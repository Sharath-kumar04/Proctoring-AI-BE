from .base import Base, Column, Integer, String, relationship
from sqlalchemy import LargeBinary

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    image = Column(LargeBinary, nullable=True)  # Changed from LONGBLOB to LargeBinary
    
    # Add relationship after Log class is defined
    logs = relationship("Log", back_populates="user")

# Add relationship to Log class after User class is defined
from .logs import Log
Log.user = relationship("User", back_populates="logs")
