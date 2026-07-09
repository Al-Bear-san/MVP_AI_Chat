import aiohttp
from aiohttp import web
from datetime import datetime
import structlog

from booking_bot.core.message_bus import UnifiedMessage, UnifiedResponse, Channel
from booking_bot.core.config import settings

logger = structlog.get_logger()


class MAXAdapter:
    BASE_URL = "https://api.max.ru/bots"
    
    def __init__(self, message_bus):
        if not settings.max_bot_token:
            logger.warning("max_adapter_disabled", reason="no_token")
            self.enabled = False
            return
        
        self.enabled = True
        self.token = settings.max_bot_token
        self.message_bus = message_bus
        self.session = None
    
    async def _setup(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    async def webhook_handler(self, request: web.Request):
        try:
            data = await request.json()
            unified = UnifiedMessage(
                channel=Channel.MAX,
                external_user_id=str(data['user']['id']),
                channel_chat_id=str(data['chat']['id']),
                text=data.get('text'),
                timestamp=datetime.fromisoformat(data['timestamp'])
            )
            response = await self.message_bus.process(unified)
            await self._send_response(data['chat']['id'], response)
            return web.Response(status=200)
        except Exception as e:
            logger.error("max_webhook_error", error=str(e))
            return web.Response(status=500)
    
    async def _send_response(self, chat_id: str, response: UnifiedResponse):
        if not self.session:
            await self._setup()
        
        try:
            async with self.session.post(
                f"{self.BASE_URL}/messages.send",
                json={
                    "chat_id": chat_id,
                    "text": response.text
                }
            ) as resp:
                resp.raise_for_status()
                logger.info("max_message_sent", chat_id=chat_id)
        except Exception as e:
            logger.error("max_send_error", error=str(e), chat_id=chat_id)
    
    async def start(self):
        if not self.enabled:
            logger.info("max_adapter_skipped")
            return
        
        await self._setup()
        logger.info("max_adapter_started")