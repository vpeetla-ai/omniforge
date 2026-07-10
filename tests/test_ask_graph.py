
import pytest
from omniforge.config import Settings
from omniforge.graph.ask import run_ab, run_ask
from omniforge.models import MissionInput, RouteMode


@pytest.mark.asyncio
async def test_ask_mock():
    settings = Settings(omniforge_mode="mock", omniforge_budget_usd=1.0)
    resp = await run_ask(MissionInput(text="Compare Groq vs OpenAI for agent routing"), settings)
    assert resp.answer
    assert "synthesizer" in resp.agents_run
    assert len(resp.waterfall) >= 3
    assert all(d.step for d in resp.waterfall)
    # routed mode should use different buckets across steps
    buckets = {d.bucket for d in resp.waterfall}
    assert len(buckets) >= 2


@pytest.mark.asyncio
async def test_ask_with_voice():
    settings = Settings(omniforge_mode="mock")
    resp = await run_ask(
        MissionInput(voice_transcript="Explain continuous batching in one paragraph"),
        settings,
    )
    assert resp.answer
    assert resp.mocked is True


@pytest.mark.asyncio
async def test_ab():
    settings = Settings(omniforge_mode="mock")
    out = await run_ab(MissionInput(text="What is OmniForge?"), settings)
    assert "routed" in out and "single" in out
    assert "delta" in out


@pytest.mark.asyncio
async def test_routing_invariant_buckets():
    """Routed mode: web uses fast, analysis uses reasoning."""
    from omniforge.brain.policy import AGENT_BUCKETS

    settings = Settings(omniforge_mode="mock")
    resp = await run_ask(MissionInput(text="Market analysis for Stripe", preset="war_room"), settings)
    by_step = {d.step: d for d in resp.waterfall}
    if "web" in by_step:
        assert by_step["web"].bucket == AGENT_BUCKETS["web"]
    if "analysis" in by_step:
        assert by_step["analysis"].bucket == AGENT_BUCKETS["analysis"]
