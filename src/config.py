"""Configuration management via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM Provider
    anthropic_api_key: str = ""
    model_name: str = "claude-3-5-haiku-20241022"

    # Langfuse observability (optional)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0

    # Paths
    database_path: str = "data/mafia.db"
    logs_dir: str = "logs"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
