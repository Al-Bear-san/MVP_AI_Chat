from openai import AsyncOpenAI
import structlog

from booking_bot.models.booking import Booking
from booking_bot.core.config import settings

logger = structlog.get_logger()


class AIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_reminder(self, booking: Booking) -> str:
        prompt = f"""Сгенерируй короткое напоминание о брони для гостя.
Имя: {booking.guest_name}
Дата: {booking.booking_datetime.strftime('%d.%m.%Y в %H:%M')}
Гостей: {booking.guests_count}
Ресторан: {settings.restaurant_name}

Тон: дружелюбный, короткий, с эмодзи. Максимум 100 символов."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("ai_generation_error", error=str(e))
            return f"Напоминаем о вашей брони на {booking.booking_datetime.strftime('%d.%m.%Y в %H:%M')}!"
    
    async def generate_faq_answer(self, question: str) -> str:
        prompt = f"""Ответь на вопрос клиента ресторана кратко и дружелюбно:
{question}

Максимум 150 символов."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("ai_faq_error", error=str(e))
            return "Извините, не могу ответить на этот вопрос. Позвоните нам: +7 (999) 123-45-67"