from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Local development reads the root .env file. Render environment variables
    # take precedence automatically and no .env file is required in production.
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")
    demo_mode: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    allowed_origins: str = ""
    max_upload_mb: int = Field(default=5, ge=1, le=10)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    cookie_secure: bool = False
    audio_detector_url: str = ""
    audio_detector_token: str = ""
    max_audio_mb: int = Field(default=10, ge=1, le=25)


@lru_cache
def get_settings() -> Settings:
    return Settings()
