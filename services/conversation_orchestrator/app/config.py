from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_ttl_seconds: int = Field(default=3600, alias="SESSION_TTL_SECONDS")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    backend_api_url: HttpUrl | str = Field(
        default="http://backend-api:8082", alias="BACKEND_API_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
