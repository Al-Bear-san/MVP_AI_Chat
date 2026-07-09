from abc import ABC, abstractmethod
from booking_bot.core.message_bus import UnifiedMessage, UnifiedResponse


class BaseAdapter(ABC):
    """Базовый класс для всех канальных адаптеров"""
    
    def __init__(self, message_bus):
        self.message_bus = message_bus
    
    @abstractmethod
    async def start(self):
        """Запуск адаптера"""
        pass
    
    @abstractmethod
    async def _send_response(self, chat_id: str, response: UnifiedResponse):
        """Отправка ответа в канал"""
        pass
    
    async def _handle_message(self, message: UnifiedMessage) -> UnifiedResponse:
        """Обработка входящего сообщения"""
        return await self.message_bus.process(message)