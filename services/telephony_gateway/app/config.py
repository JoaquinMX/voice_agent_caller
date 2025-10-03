from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the telephony gateway service."""

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    orchestrator_url: HttpUrl | str = Field(
        default="http://conversation-orchestrator:8081", alias="ORCHESTRATOR_URL"
    )
    backend_api_url: HttpUrl | str = Field(
        default="http://backend-api:8082", alias="BACKEND_API_URL"
    )
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    polly_voice_id: str = Field(default="Lucia", alias="POLLY_VOICE_ID")
    polly_engine: Literal["standard", "neural"] = Field(default="neural", alias="POLLY_ENGINE")
    transcribe_language_code: str = Field(default="es-MX", alias="TRANSCRIBE_LANGUAGE_CODE")
    audio_cache_ttl_seconds: int = Field(default=3600, alias="AUDIO_CACHE_TTL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
