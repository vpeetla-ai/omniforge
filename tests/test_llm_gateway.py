"""LLM gateway plane wiring (no live gateway required)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from omniforge.brain.cascade import complete, llm_gateway_enabled
from omniforge.config import Settings, get_settings
from omniforge.models import RouteBucket


def test_llm_gateway_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LLM_GATEWAY_URL", raising=False)
    get_settings.cache_clear()
    assert llm_gateway_enabled() is False
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_complete_routes_through_gateway(monkeypatch):
    monkeypatch.setenv("LLM_GATEWAY_URL", "http://127.0.0.1:8100/v1")
    monkeypatch.setenv("LLM_GATEWAY_TENANT_ID", "omniforge-test")
    get_settings.cache_clear()

    settings = Settings(
        omniforge_mode="live",
        llm_gateway_url="http://127.0.0.1:8100/v1",
        llm_gateway_tenant_id="omniforge-test",
        openai_api_key="",
        anthropic_api_key="",
        groq_api_key="",
        google_api_key="",
    )

    with patch("omniforge.brain.cascade._gateway", new=AsyncMock(return_value="gateway ok")) as mock_gw:
        result = await complete(
            step="planner",
            bucket=RouteBucket.FAST,
            system="sys",
            user="hello",
            reason="test",
            settings=settings,
        )

    assert result.text == "gateway ok"
    assert result.decision.provider == "aegis-llm-gateway"
    assert result.decision.mocked is False
    mock_gw.assert_awaited_once()
    get_settings.cache_clear()


def test_ops_metrics_shows_llm_gateway(monkeypatch):
    monkeypatch.delenv("LLM_GATEWAY_URL", raising=False)
    get_settings.cache_clear()
    client = TestClient(app)
    resp = client.get("/v1/ops/metrics")
    assert resp.status_code == 200
    gw = resp.json()["extra"]["llm_gateway"]
    assert gw["plane"] == "aegis-llm-gateway"
    get_settings.cache_clear()
