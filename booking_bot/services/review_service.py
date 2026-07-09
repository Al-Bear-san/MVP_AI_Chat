from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import structlog

from booking_bot.repositories.booking_repo import BookingRepository
from booking_bot.integrations.ai_service import AIService
from booking_bot.database import async_session

logger = structlog.get_logger()


class ReminderService:
    def __init__(self, ai_service: AIService, telegram_bot, vk_api):
        self.ai_service = ai_service
        self.telegram_bot = telegram_bot
        self.vk_api = vk_api
        self.scheduler = AsyncIOScheduler()
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """Настройка расписания проверок"""
        self.scheduler.add_job(
            self._check_reminders,
            'interval',
            minutes=15,
            id='check_reminders'
        )
    
    async def _check_reminders(self):
        """Проверка броней для отправки напоминаний"""
        async with async_session() as db:
            repo = BookingRepository(db)
            upcoming_bookings = await repo.get_upcoming(hours=2)
            
            for booking in upcoming_bookings:
                if self._should_send_reminder(booking):
                    await self._send_reminder(booking)
    
    async def _send_reminder(self, booking):
        """Отправка напоминания через соответствующий канал"""
        reminder_text = await self.ai_service.generate_reminder(booking)
        
        try:
            if booking.channel.value == "telegram":
                await self.telegram_bot.send_message(
                    chat_id=int(booking.external_user_id),
                    text=reminder_text
                )
            elif booking.channel.value == "vk":
                self.vk_api.messages.send(
                    user_id=int(booking.external_user_id),
                    message=reminder_text,
                    random_id=0
                )
            
            logger.info("reminder_sent", booking_id=booking.id, channel=booking.channel.value)
        except Exception as e:
            logger.error("reminder_error", error=str(e), booking_id=booking.id)
    
    def _should_send_reminder(self, booking) -> bool:
        """Проверка, нужно ли отправлять напоминание"""
        time_diff = booking.booking_datetime - datetime.utcnow()
        return timedelta(hours=1.5) <= time_diff <= timedelta(hours=2.5)
    
    async def start(self):
        """Запуск сервиса напоминаний"""
        self.scheduler.start()
        logger.info("reminder_service_started")
    
    async def stop(self):
        """Остановка сервиса"""
        self.scheduler.shutdown()
        logger.info("reminder_service_stopped")