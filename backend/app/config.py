"""Application settings, loaded from environment variables.

Using pydantic-settings gives us validation and typed access to config,
so a missing/invalid value fails fast at startup instead of at request time.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://linkly:linkly_dev_password@localhost:5432/linkly"
    redis_url: str = "redis://localhost:6379/0"
    base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    # Cache TTL for code -> url lookups, in seconds.
    cache_ttl_seconds: int = 3600

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings are parsed once per process."""
    return Settings()
