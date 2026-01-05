"""Configuration management via environment variables."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Provider
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    model_name: str = "gemini-3-flash-preview"

    # Langfuse observability (optional)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_base_url: str = ""

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0

    # Paths
    logs_dir: str = "logs"

    @model_validator(mode="after")
    def _apply_langfuse_base_url(self) -> "Settings":
        if self.langfuse_base_url and (
            not self.langfuse_host or self.langfuse_host == "https://cloud.langfuse.com"
        ):
            self.langfuse_host = self.langfuse_base_url
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
