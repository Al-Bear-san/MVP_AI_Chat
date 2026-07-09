# booking_bot/core/enums.py
from enum import Enum


class Channel(str, Enum):
    TELEGRAM = "telegram"
    VK = "vk"
    MAX = "max"