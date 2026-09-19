from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    demo_mode: bool = True
    gemini_api_key: str = ""
    allowed_origins: str = ""
    max_upload_mb: int = Field(default=5, ge=1, le=10)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)


@lru_cache
def get_settings() -> Settings:
    return Settings()
