from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
import structlog

from booking_bot.models.booking import Booking
from booking_bot.core.message_bus import UnifiedMessage, UnifiedResponse, Channel
from booking_bot.services.state_service import StateService
from booking_bot.integrations.google_calendar import GoogleCalendarService
from booking_bot.integrations.ai_service import AIService
from booking_bot.core.config import settings

logger = structlog.get_logger()


class BookingService:
    def __init__(
        self,
        db: AsyncSession,
        state_service: StateService,
        calendar_service: Optional[GoogleCalendarService] = None,
        ai_service: Optional[AIService] = None
    ):
        self.db = db
        self.state_service = state_service
        self.calendar_service = calendar_service
        self.ai_service = ai_service
    
    async def handle(self, message: UnifiedMessage) -> UnifiedResponse:
        state = await self.state_service.get_user_state(message.channel, message.external_user_id)
        
        if state == "awaiting_name":
            return await self._process_name(message)
        elif state == "awaiting_phone":
            return await self._process_phone(message)
        elif state == "awaiting_guests":
            return await self._process_guests(message)
        elif state == "awaiting_datetime":
            return await self._process_datetime(message)
        elif message.payload and message.payload.get("callback_data"):
            return await self._handle_callback(message)
        else:
            return await self._start_booking(message)
    
    async def _start_booking(self, message: UnifiedMessage) -> UnifiedResponse:
        await self.state_service.set_user_state(
            message.channel, message.external_user_id, "awaiting_name"
        )
        
        return UnifiedResponse(
            text="🎉 <b>Отлично! Давайте забронируем столик.</b>\n\n"
                 "Как вас зовут?",
            parse_mode="HTML"
        )
    
    async def _process_name(self, message: UnifiedMessage) -> UnifiedResponse:
        if not message.text or len(message.text) < 2:
            return UnifiedResponse(text="Пожалуйста, введите ваше имя (минимум 2 символа).")
        
        await self.state_service.set_user_data(
            message.channel, message.external_user_id, "name", message.text
        )
        await self.state_service.set_user_state(
            message.channel, message.external_user_id, "awaiting_phone"
        )
        
        return UnifiedResponse(
            text=f"Приятно познакомиться, {message.text}! 📱\n\n"
                 "Укажите ваш номер телефона для связи."
        )
    
    async def _process_phone(self, message: UnifiedMessage) -> UnifiedResponse:
        if not message.text or not self._validate_phone(message.text):
            return UnifiedResponse(
                text="❌ Неверный формат телефона. Пример: +79991234567"
            )
        
        await self.state_service.set_user_data(
            message.channel, message.external_user_id, "phone", message.text
        )
        await self.state_service.set_user_state(
            message.channel, message.external_user_id, "awaiting_guests"
        )
        
        return UnifiedResponse(
            text="👥 Сколько гостей будет с вами? (1-20 человек)"
        )
    
    async def _process_guests(self, message: UnifiedMessage) -> UnifiedResponse:
        try:
            guests = int(message.text)
            if not 1 <= guests <= 20:
                raise ValueError
        except (ValueError, TypeError):
            return UnifiedResponse(text="Пожалуйста, введите число от 1 до 20.")
        
        await self.state_service.set_user_data(
            message.channel, message.external_user_id, "guests", guests
        )
        await self.state_service.set_user_state(
            message.channel, message.external_user_id, "awaiting_datetime"
        )
        
        return UnifiedResponse(
            text="📅 На какую дату и время бронируем?\n\n"
                 "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
                 "Пример: 15.07.2026 19:00"
        )
    
    async def _process_datetime(self, message: UnifiedMessage) -> UnifiedResponse:
        try:
            booking_dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
            if booking_dt < datetime.now():
                return UnifiedResponse(text="❌ Дата должна быть в будущем.")
        except ValueError:
            return UnifiedResponse(
                text="❌ Неверный формат. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ"
            )
        
        # Получаем все данные
        name = await self.state_service.get_user_data(message.channel, message.external_user_id, "name")
        phone = await self.state_service.get_user_data(message.channel, message.external_user_id, "phone")
        guests = await self.state_service.get_user_data(message.channel, message.external_user_id, "guests")
        
        # Создаем бронь
        booking = Booking(
            channel=message.channel,
            external_user_id=message.external_user_id,
            guest_name=name,
            guest_phone=phone,
            guests_count=guests,
            booking_datetime=booking_dt,
            status="confirmed"
        )
        
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        
        # Создаем событие в календаре
        if self.calendar_service:
            try:
                await self.calendar_service.create_event(booking)
            except Exception as e:
                logger.error("calendar_error", error=str(e))
        
        # Очищаем состояние
        await self.state_service.clear_user_state(message.channel, message.external_user_id)
        
        # Генерируем подтверждение с AI
        confirmation_text = f"✅ <b>Бронь подтверждена!</b>\n\n"
        confirmation_text += f"👤 Имя: {name}\n"
        confirmation_text += f"📱 Телефон: {phone}\n"
        confirmation_text += f"👥 Гостей: {guests}\n"
        confirmation_text += f"📅 Дата: {booking_dt.strftime('%d.%m.%Y в %H:%M')}\n"
        confirmation_text += f"🏢 Ресторан: {settings.restaurant_name}\n\n"
        confirmation_text += f"Номер брони: #{booking.id}\n\n"
        confirmation_text += "Ждем вас! 🎉"
        
        logger.info(
            "booking_created",
            booking_id=booking.id,
            channel=message.channel.value,
            guest_name=name
        )
        
        return UnifiedResponse(text=confirmation_text, parse_mode="HTML")
    
    async def _handle_callback(self, message: UnifiedMessage) -> UnifiedResponse:
        callback_data = message.payload.get("callback_data")
        
        if callback_data == "cancel_booking":
            await self.state_service.clear_user_state(message.channel, message.external_user_id)
            return UnifiedResponse(text="❌ Бронирование отменено.")
        
        return UnifiedResponse(text="Неизвестная команда.")
    
    def _validate_phone(self, phone: str) -> bool:
        import re
        pattern = r'^\+?[0-9]{10,15}$'
        return bool(re.match(pattern, phone.replace(" ", "").replace("-", "")))
    