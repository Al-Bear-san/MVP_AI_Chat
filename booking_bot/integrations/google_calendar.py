from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import timedelta
import structlog

from booking_bot.models.booking import Booking

logger = structlog.get_logger()


class GoogleCalendarService:
    def __init__(self, credentials: Credentials, calendar_id: str):
        self.service = build('calendar', 'v3', credentials=credentials)
        self.calendar_id = calendar_id
    
    async def create_event(self, booking: Booking):
        event = {
            'summary': f"Бронь: {booking.guest_name} ({booking.guests_count} гостей)",
            'start': {
                'dateTime': booking.booking_datetime.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'end': {
                'dateTime': (booking.booking_datetime + timedelta(hours=2)).isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'description': f"Телефон: {booking.guest_phone}\nКанал: {booking.channel.value}\nID брони: {booking.id}",
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }
        
        try:
            result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            logger.info("calendar_event_created", event_id=result.get('id'))
            return result
        except Exception as e:
            logger.error("calendar_event_error", error=str(e))
            raise
        