from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
import structlog

from booking_bot.core.message_bus import UnifiedMessage, UnifiedResponse, Channel
from booking_bot.core.config import settings

logger = structlog.get_logger()


class TelegramAdapter:
    def __init__(self, message_bus):
        self.bot = Bot(token=settings.telegram_token)
        self.dp = Dispatcher()
        self.router = Router()
        self.message_bus = message_bus
        self._setup_handlers()
    
    def _setup_handlers(self):
        self.router.message.register(self._handle_message, F.text)
        self.router.message.register(self._handle_command, Command("start", "help", "cancel"))
        self.router.callback_query.register(self._handle_callback, F.data)
        self.dp.include_router(self.router)
    
    async def _handle_command(self, message: Message):
        unified = UnifiedMessage(
            channel=Channel.TELEGRAM,
            external_user_id=str(message.from_user.id),
            channel_chat_id=str(message.chat.id),
            text=message.text,
            payload={"command": message.text[1:]}
        )
        response = await self.message_bus.process(unified)
        await self._send_response(message.chat.id, response)
    
    async def _handle_message(self, message: Message):
        unified = UnifiedMessage(
            channel=Channel.TELEGRAM,
            external_user_id=str(message.from_user.id),
            channel_chat_id=str(message.chat.id),
            text=message.text,
            timestamp=message.date
        )
        response = await self.message_bus.process(unified)
        await self._send_response(message.chat.id, response)
    
    async def _handle_callback(self, callback: CallbackQuery):
        unified = UnifiedMessage(
            channel=Channel.TELEGRAM,
            external_user_id=str(callback.from_user.id),
            channel_chat_id=str(callback.message.chat.id),
            payload={"callback_data": callback.data}
        )
        response = await self.message_bus.process(unified)
        await self._send_response(callback.message.chat.id, response)
        await callback.answer()
    
    async def _send_response(self, chat_id: int, response: UnifiedResponse):
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=response.text,
                parse_mode=ParseMode.HTML if response.parse_mode else None
            )
            logger.info("telegram_message_sent", chat_id=chat_id)
        except Exception as e:
            logger.error("telegram_send_error", error=str(e), chat_id=chat_id)
    
    async def start(self):
        logger.info("telegram_adapter_started")
        await self.dp.start_polling(self.bot)