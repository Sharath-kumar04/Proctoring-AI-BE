from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import relationship
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    image = Column(LargeBinary, nullable=True)
    
    # Relationship with logs
    logs = relationship("Log", back_populates="user")
