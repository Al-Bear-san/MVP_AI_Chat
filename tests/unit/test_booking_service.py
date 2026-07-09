import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from booking_bot.services.booking_service import BookingService
from booking_bot.core.message_bus import UnifiedMessage, Channel
from booking_bot.models.booking import Booking


@pytest.mark.asyncio
async def test_start_booking():
    db = AsyncMock()
    state_service = AsyncMock()
    booking_service = BookingService(db, state_service)
    
    message = UnifiedMessage(
        channel=Channel.TELEGRAM,
        external_user_id="123",
        channel_chat_id="123",
        text="забронировать",
        timestamp=datetime.utcnow()
    )
    
    response = await booking_service.handle(message)
    
    assert "забронируем" in response.text.lower()
    state_service.set_user_state.assert_called_once()


@pytest.mark.asyncio
async def test_process_name():
    db = AsyncMock()
    state_service = AsyncMock()
    booking_service = BookingService(db, state_service)
    
    message = UnifiedMessage(
        channel=Channel.TELEGRAM,
        external_user_id="123",
        channel_chat_id="123",
        text="Иван",
        timestamp=datetime.utcnow()
    )
    
    state_service.get_user_state.return_value = "awaiting_name"
    
    response = await booking_service.handle(message)
    
    assert "Иван" in response.text
    state_service.set_user_data.assert_called_once()


@pytest.mark.asyncio
async def test_validate_phone():
    db = AsyncMock()
    state_service = AsyncMock()
    booking_service = BookingService(db, state_service)
    
    assert booking_service._validate_phone("+79991234567") is True
    assert booking_service._validate_phone("89991234567") is True
    assert booking_service._validate_phone("123") is False
    assert booking_service._validate_phone("abc") is False