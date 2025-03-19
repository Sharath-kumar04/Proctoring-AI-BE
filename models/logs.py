from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    log = Column(String(1000))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship with user
    user = relationship("User", back_populates="logs")
