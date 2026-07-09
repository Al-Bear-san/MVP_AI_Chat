from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Telegram
    telegram_token: str
    telegram_admin_ids: list[int] = []
    
    # VK
    vk_group_token: Optional[str] = None
    vk_group_id: Optional[int] = None
    vk_confirmation_token: Optional[str] = None
    
    # MAX
    max_bot_token: Optional[str] = None
    
    # Database
    db_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/booking"
    redis_url: str = "redis://localhost:6379/0"
    
    # Integrations
    google_credentials_path: Optional[str] = None
    google_calendar_id: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    
    # App
    app_name: str = "Booking Bot"
    debug: bool = False
    restaurant_name: str = "Наш Ресторан"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()