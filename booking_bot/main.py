import asyncio
import structlog
from contextlib import asynccontextmanager

from booking_bot.core.config import settings
from booking_bot.core.logging import setup_logging
from booking_bot.core.message_bus import MessageBus, UnifiedMessage, UnifiedResponse
from booking_bot.services.state_service import StateService
from booking_bot.adapters.telegram_adapter import TelegramAdapter
from booking_bot.adapters.vk_adapter import VKAdapter
from booking_bot.adapters.max_adapter import MAXAdapter
from booking_bot.integrations.google_calendar import GoogleCalendarService
from booking_bot.integrations.ai_service import AIService
from booking_bot.database import init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan():
    # Инициализация
    setup_logging()
    logger.info("app_starting", app_name=settings.app_name)
    
    # Инициализация БД
    await init_db()
    logger.info("database_initialized")
    
    # Инициализация сервисов
    state_service = StateService(settings.redis_url)
    message_bus = MessageBus(state_service)
    
    # Инициализация интеграций
    calendar_service = None
    if settings.google_credentials_path and settings.google_calendar_id:
        try:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                settings.google_credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            calendar_service = GoogleCalendarService(credentials, settings.google_calendar_id)
            logger.info("google_calendar_initialized")
        except Exception as e:
            logger.error("google_calendar_init_error", error=str(e))
    
    ai_service = None
    if settings.openai_api_key:
        ai_service = AIService(settings.openai_api_key)
        logger.info("ai_service_initialized")
    
    message_bus.set_services(calendar_service, ai_service)
    
    # Инициализация адаптеров
    adapters = []
    
    telegram_adapter = TelegramAdapter(message_bus)
    adapters.append(telegram_adapter.start())
    
    vk_adapter = VKAdapter(message_bus)
    adapters.append(vk_adapter.start())
    
    max_adapter = MAXAdapter(message_bus)
    adapters.append(max_adapter.start())
    
    logger.info("all_adapters_started")
    
    yield
    
    logger.info("app_stopping")


async def main():
    async with lifespan():
        try:
            await asyncio.gather(*[
                TelegramAdapter(MessageBus(StateService(settings.redis_url))).start(),
                VKAdapter(MessageBus(StateService(settings.redis_url))).start(),
                MAXAdapter(MessageBus(StateService(settings.redis_url))).start()
            ])
        except KeyboardInterrupt:
            logger.info("shutdown_requested")
        except Exception as e:
            logger.error("fatal_error", error=str(e))
            raise


if __name__ == "__main__":
    asyncio.run(main())