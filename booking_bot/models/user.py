from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from booking_bot.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_user_id = Column(String, nullable=False, unique=True, index=True)
    channel = Column(String, nullable=False)
    name = Column(String)
    phone = Column(String)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, external_id={self.external_user_id})>"