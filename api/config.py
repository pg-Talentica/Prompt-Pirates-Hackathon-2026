"""Application configuration loaded from environment variables.

All config is read from env; no hardcoded secrets. See .env.example for required keys.
"""

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator
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

    # Guardrails (Task-006): no hardcoded phrases; API + config only
    guardrails_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="When confidence below this, route to escalation",
    )
    guardrails_escalate_on_no_answer: bool = Field(
        default=True,
        description="When response is structured no_answer (I don't know), escalate",
    )
    guardrails_escalation_policy: str = Field(
        default="[]",
        description="JSON array of rules e.g. [{\"when\": \"no_answer\", \"then\": \"escalate\"}]",
    )

    # RAG: max distance for relevance (L2; higher = less similar). Above this = out of context.
    # Looser = more domain queries pass (e.g. disbursement); tighter = blocks off-topic (e.g. "Who is Raghu?").
    rag_max_distance: float = Field(
        default=1.2,
        ge=0.0,
        le=10.0,
        description="Retrieval relevance threshold; results with distance above this are discarded",
    )
    # Synthesis gate: best result must have distance <= this to answer; else say I don't know.
    # 1.1 allows disbursement/runbook matches; "Who is Raghu?" typically > 1.3 to any loan doc.
    rag_confidence_max_distance: float = Field(
        default=1.1,
        ge=0.0,
        le=10.0,
        description="Best retrieval result must be within this distance to answer; else out-of-context",
    )

    @field_validator("guardrails_escalation_policy", mode="before")
    @classmethod
    def parse_escalation_policy(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        import json
        return json.dumps(v) if v is not None else "[]"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (env loaded once)."""
    return Settings()
