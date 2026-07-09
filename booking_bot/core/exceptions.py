class BookingBotError(Exception):
    """Базовое исключение для бота"""
    pass


class BookingValidationError(BookingBotError):
    """Ошибка валидации данных брони"""
    pass


class ChannelError(BookingBotError):
    """Ошибка канала связи"""
    pass


class IntegrationError(BookingBotError):
    """Ошибка интеграции с внешним сервисом"""
    pass


class StateError(BookingBotError):
    """Ошибка состояния пользователя"""
    pass