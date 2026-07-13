"""Environment settings — self-contained by default; optional plane connection via LLM_GATEWAY_URL."""
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
    google_api_key: str = ""

    # Federated LLM gateway plane (aegis-llm-gateway) — optional; preferred when set
    llm_gateway_url: str = ""  # e.g. http://127.0.0.1:8100/v1
    llm_gateway_api_key: str = ""
    llm_gateway_tenant_id: str = "omniforge"

    omniforge_fast_model: str = "llama-3.3-70b-versatile"
    omniforge_structured_model: str = "gpt-4o-mini"
    omniforge_reasoning_model: str = "claude-sonnet-4-20250514"
    omniforge_vision_model: str = "gpt-4o"
    omniforge_google_model: str = "gemini-2.0-flash"

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
