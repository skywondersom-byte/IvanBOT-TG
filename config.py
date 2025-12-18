from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import logging

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore' # Ігнорувати зайві змінні в .env
    )

    BOT_TOKEN: str
    GEMINI_API_KEY: str
    SOURCE_CHANNEL_ID: int
    TARGET_CHANNEL_ID: int
    
    # Опціональні параметри
    LOG_LEVEL: str = "INFO"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    @field_validator('BOT_TOKEN')
    @classmethod
    def validate_bot_token(cls, v):
        if not v or ":" not in v:
            raise ValueError("Невалідний формат BOT_TOKEN")
        return v
    
    @field_validator('SOURCE_CHANNEL_ID', 'TARGET_CHANNEL_ID')
    @classmethod
    def validate_channel_ids(cls, v):
        # ID каналів в Telegram зазвичай від'ємні
        if v > 0:
            logging.warning(f"ID каналу {v} позитивний. Переконайтеся, що це вірно (для каналів зазвичай використовується -100...).")
        return v

settings = Settings()