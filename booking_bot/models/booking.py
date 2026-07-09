from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime

from booking_bot.database import Base
from booking_bot.core.enums import Channel


class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(SQLEnum(Channel), nullable=False)
    external_user_id = Column(String, nullable=False, index=True)
    guest_name = Column(String, nullable=False)
    guest_phone = Column(String, nullable=False)
    guests_count = Column(Integer, nullable=False)
    booking_datetime = Column(DateTime, nullable=False, index=True)
    status = Column(String, default="confirmed", nullable=False)
    extra_data = Column("metadata", JSONB, default=dict)  # ← ИСПРАВЛЕНО
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Booking(id={self.id}, guest={self.guest_name}, date={self.booking_datetime})>"