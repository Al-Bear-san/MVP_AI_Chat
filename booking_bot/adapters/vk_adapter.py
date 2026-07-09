from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from datetime import datetime
import asyncio
import structlog

from booking_bot.core.message_bus import UnifiedMessage, UnifiedResponse, Channel
from booking_bot.core.config import settings

logger = structlog.get_logger()


class VKAdapter:
    def __init__(self, message_bus):
        if not settings.vk_group_token or not settings.vk_group_id:
            logger.warning("vk_adapter_disabled", reason="no_credentials")
            self.enabled = False
            return
        
        self.enabled = True
        self.vk_session = VkApi(token=settings.vk_group_token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, settings.vk_group_id)
        self.group_id = settings.vk_group_id
        self.message_bus = message_bus
    
    async def _handle_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message
            unified = UnifiedMessage(
                channel=Channel.VK,
                external_user_id=str(msg['from_id']),
                channel_chat_id=str(msg['peer_id']),
                text=msg.get('text', ''),
                timestamp=datetime.fromtimestamp(msg['date'])
            )
            response = await self.message_bus.process(unified)
            await self._send_response(msg['peer_id'], response)
    
    async def _send_response(self, peer_id: int, response: UnifiedResponse):
        try:
            self.vk.messages.send(
                peer_id=peer_id,
                message=response.text,
                random_id=0
            )
            logger.info("vk_message_sent", peer_id=peer_id)
        except Exception as e:
            logger.error("vk_send_error", error=str(e), peer_id=peer_id)
    
    async def start(self):
        if not self.enabled:
            logger.info("vk_adapter_skipped")
            return
        
        logger.info("vk_adapter_started")
        while True:
            try:
                for event in self.longpoll.listen():
                    asyncio.create_task(self._handle_event(event))
            except Exception as e:
                logger.error("vk_longpoll_error", error=str(e))
                await asyncio.sleep(5)