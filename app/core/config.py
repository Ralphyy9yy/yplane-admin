from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig", extra="ignore")
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ticket_booking_db"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ADMIN_EMAIL: str = "admin@ticketadmin.com"
    ADMIN_PASSWORD: str = "admin123"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
