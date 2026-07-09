import redis.asyncio as redis
from typing import Optional, Any
import json

from booking_bot.core.enums import Channel


class StateService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def set_user_state(self, channel: Channel, user_id: str, state: str, ttl: int = 3600):
        key = f"state:{channel.value}:{user_id}"
        await self.redis.setex(key, ttl, state)
    
    async def get_user_state(self, channel: Channel, user_id: str) -> Optional[str]:
        key = f"state:{channel.value}:{user_id}"
        return await self.redis.get(key)
    
    async def clear_user_state(self, channel: Channel, user_id: str):
        key = f"state:{channel.value}:{user_id}"
        await self.redis.delete(key)
        
        data_key = f"data:{channel.value}:{user_id}"
        await self.redis.delete(data_key)
    
    async def set_user_data(self, channel: Channel, user_id: str, field: str, value: Any, ttl: int = 3600):
        key = f"data:{channel.value}:{user_id}"
        data = await self.redis.get(key)
        data_dict = json.loads(data) if data else {}
        data_dict[field] = value
        await self.redis.setex(key, ttl, json.dumps(data_dict))
    
    async def get_user_data(self, channel: Channel, user_id: str, field: str) -> Optional[Any]:
        key = f"data:{channel.value}:{user_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        data_dict = json.loads(data)
        return data_dict.get(field)
    
    async def rate_limit(self, channel: Channel, user_id: str, limit: int = 10, window: int = 60) -> bool:
        key = f"rate:{channel.value}:{user_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current <= limit