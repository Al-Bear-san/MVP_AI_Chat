import re
from datetime import datetime
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    pattern = r'^\+?[0-9]{10,15}$'
    cleaned = phone.replace(" ", "").replace("-", "")
    return bool(re.match(pattern, cleaned))


def validate_datetime(dt_string: str) -> Optional[datetime]:
    """Валидация даты и времени"""
    try:
        dt = datetime.strptime(dt_string, "%d.%m.%Y %H:%M")
        if dt < datetime.now():
            return None
        return dt
    except ValueError:
        return None


def validate_guests_count(count: str) -> Optional[int]:
    """Валидация количества гостей"""
    try:
        guests = int(count)
        if 1 <= guests <= 20:
            return guests
        return None
    except (ValueError, TypeError):
        return None


def validate_name(name: str) -> bool:
    """Валидация имени"""
    return len(name.strip()) >= 2 and name.replace(" ", "").isalpha()