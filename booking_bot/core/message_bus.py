from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, Any


class Channel(str, Enum):
    TELEGRAM = "telegram"
    VK = "vk"
    MAX = "max"


class UnifiedMessage(BaseModel):
    channel: Channel
    external_user_id: str
    channel_chat_id: str
    text: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attachments: list[str] = Field(default_factory=list)


class UnifiedResponse(BaseModel):
    text: str
    buttons: list[dict[str, Any]] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    reply_to_message_id: Optional[str] = None
    parse_mode: Optional[str] = None


from typing import Optional
import structlog

from booking_bot.services.booking_service import BookingService
from booking_bot.services.state_service import StateService
from booking_bot.database import async_session

logger = structlog.get_logger()


class MessageBus:
    def __init__(self, state_service: StateService):
        self.state_service = state_service
        self.booking_service = None
        self.calendar_service = None
        self.ai_service = None
    
    def set_services(self, calendar_service=None, ai_service=None):
        self.calendar_service = calendar_service
        self.ai_service = ai_service
    
    async def process(self, message: UnifiedMessage) -> UnifiedResponse:
        try:
            # Rate limiting
            if not await self.state_service.rate_limit(message.channel, message.external_user_id):
                return UnifiedResponse(text="⏳ Слишком много запросов. Подождите минуту.")
            
            # Определяем состояние пользователя
            state = await self.state_service.get_user_state(message.channel, message.external_user_id)
            
            # Команды
            if message.payload and message.payload.get("command") == "start":
                return await self._handle_start(message)
            elif message.payload and message.payload.get("command") == "cancel":
                await self.state_service.clear_user_state(message.channel, message.external_user_id)
                return UnifiedResponse(text="❌ Действие отменено.")
            
            # Бронирование
            if state or (message.text and "брон" in message.text.lower()):
                async with async_session() as db:
                    booking_service = BookingService(
                        db=db,
                        state_service=self.state_service,
                        calendar_service=self.calendar_service,
                        ai_service=self.ai_service
                    )
                    return await booking_service.handle(message)
            
            # FAQ
            if message.text:
                if self.ai_service:
                    answer = await self.ai_service.generate_faq_answer(message.text)
                    return UnifiedResponse(text=answer)
                else:
                    return UnifiedResponse(
                        text="👋 Привет! Я помогу забронировать столик.\n\n"
                             "Напишите 'забронировать' или /start"
                    )
            
            return UnifiedResponse(
                text="👋 Привет! Я бот для бронирования столиков.\n\n"
                     "Напишите 'забронировать' или /start"
            )
        
        except Exception as e:
            logger.error("message_bus_error", error=str(e), message=message.dict())
            return UnifiedResponse(text="❌ Произошла ошибка. Попробуйте позже.")
    
    async def _handle_start(self, message: UnifiedMessage) -> UnifiedResponse:
        return UnifiedResponse(
            text=f"👋 Добро пожаловать в <b>{settings.restaurant_name}</b>!\n\n"
                 "Я помогу вам забронировать столик.\n\n"
                 "Напишите 'забронировать' или просто начните диалог!",
            parse_mode="HTML"
        )