"""Application configuration loaded from environment variables.

All config is read from env; no hardcoded secrets. See .env.example for required keys.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment (and .env file when present)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    llm_api_key: str = Field(default="", description="API key for the LLM provider")
    model: str = Field(default="gpt-4o-mini", description="Model name for all agents")

    # Server
    api_host: str = Field(default="0.0.0.0", description="Bind host for the API server")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Port for the API server")

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Runtime environment"
    )
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (env loaded once)."""
    return Settings()
