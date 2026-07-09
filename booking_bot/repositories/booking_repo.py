from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from booking_bot.models.booking import Booking


class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def get_by_id(self, booking_id: int) -> Optional[Booking]:
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, external_user_id: str) -> list[Booking]:
        result = await self.db.execute(
            select(Booking)
            .where(Booking.external_user_id == external_user_id)
            .order_by(Booking.booking_datetime.desc())
        )
        return result.scalars().all()
    
    async def get_upcoming(self, hours: int = 24) -> list[Booking]:
        now = datetime.utcnow()
        future = datetime.utcnow() + timedelta(hours=hours)
        
        result = await self.db.execute(
            select(Booking)
            .where(
                Booking.booking_datetime.between(now, future),
                Booking.status == "confirmed"
            )
        )
        return result.scalars().all()
    
    async def update_status(self, booking_id: int, status: str) -> Optional[Booking]:
        booking = await self.get_by_id(booking_id)
        if booking:
            booking.status = status
            await self.db.commit()
            await self.db.refresh(booking)
        return booking