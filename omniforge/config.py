"""Environment settings — self-contained; no sibling repo URLs required."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    omniforge_mode: str = "mock"  # mock | live

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    omniforge_fast_model: str = "llama-3.3-70b-versatile"
    omniforge_structured_model: str = "gpt-4o-mini"
    omniforge_reasoning_model: str = "claude-sonnet-4-20250514"
    omniforge_vision_model: str = "gpt-4o"

    omniforge_budget_usd: float = 0.50
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    production_strict: bool = False
    omniforge_gateway_fail_open: bool = True

    cors_origins: str = "http://localhost:3000,http://localhost:4173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def live(self) -> bool:
        return self.omniforge_mode.lower() == "live"


@lru_cache
def get_settings() -> Settings:
    return Settings()
