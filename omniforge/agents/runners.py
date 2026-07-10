
"""Specialized agents — each requests a RouteBucket via the Multi-LLM Brain."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from omniforge.brain import bucket_for_agent, complete
from omniforge.brain.policy import BUCKET_REASONS
from omniforge.config import Settings
from omniforge.mcp.bridge import call_tool
from omniforge.models import AgentResult, Mission, RouteMode
from omniforge.rag.memory import STORE


def _single(mission: Mission) -> str | None:
    if mission.mode == RouteMode.SINGLE:
        return mission.single_model or "mock"
    return None


async def run_vision(mission: Mission, image_b64: str | None, settings: Settings) -> AgentResult:
    bucket = bucket_for_agent("vision")
    if not image_b64:
        return AgentResult(agent="vision", ok=True, summary="No image provided", details={})
    result = await complete(
        step="vision",
        bucket=bucket,
        system="You describe screenshots/images for an AI architect. Be concrete.",
        user=f"Describe this image for the mission:\n{mission.question[:500]}",
        reason=BUCKET_REASONS[bucket],
        mode_single_model=_single(mission),
        image_b64=image_b64,
        settings=settings,
    )
    mission.image_caption = result.text
    return AgentResult(agent="vision", summary=result.text[:500], routing=result.decision)


async def run_web(mission: Mission, settings: Settings) -> AgentResult:
    bucket = bucket_for_agent("web")
    # Extract first URL if present for allowlisted fetch via tool
    urls = re.findall(r"https?://[^\s]+", mission.question)
    tool_bits = {}
    if urls:
        tool_bits = await call_tool("mcp_http_get", {"url": urls[0]})
    result = await complete(
        step="web",
        bucket=bucket,
        system="You are the Web agent. Summarize public signals relevant to the mission.",
        user=(
            f"Mission:\n{mission.question}\n\n"
            f"Fetched URL preview (if any): {tool_bits}\n"
            f"Image caption: {mission.image_caption or 'n/a'}"
        ),
        reason=BUCKET_REASONS[bucket],
        mode_single_model=_single(mission),
        settings=settings,
    )
    return AgentResult(
        agent="web",
        summary=result.text[:600],
        details={"tool": tool_bits, "urls": urls[:3]},
        routing=result.decision,
    )


async def run_api(mission: Mission, settings: Settings) -> AgentResult:
    bucket = bucket_for_agent("api")
    # Structured enrichment stub — public metadata style
    host = None
    urls = re.findall(r"https?://[^\s]+", mission.question)
    if urls:
        host = urlparse(urls[0]).netloc
    result = await complete(
        step="api",
        bucket=bucket,
        system="You are the API agent. Return structured JSON-like findings (keys: entity, signals, risks).",
        user=f"Mission: {mission.question}\nHost hint: {host}\nCaption: {mission.image_caption}",
        reason=BUCKET_REASONS[bucket],
        mode_single_model=_single(mission),
        settings=settings,
    )
    return AgentResult(
        agent="api",
        summary=result.text[:600],
        details={"host": host},
        routing=result.decision,
    )


async def run_data(mission: Mission, settings: Settings) -> AgentResult:
    bucket = bucket_for_agent("data")
    # Persist mission context into memory store
    STORE.upsert(mission.mission_id, mission.question)
    if mission.image_caption:
        STORE.upsert(f"{mission.mission_id}:img", mission.image_caption)
    hits = STORE.retrieve(mission.question, k=3)
    result = await complete(
        step="data",
        bucket=bucket,
        system="You are the Data/RAG agent. Use retrieved memory snippets to ground the answer.",
        user=f"Mission: {mission.question}\nRetrieved:\n" + "\n---\n".join(hits or ["(empty store)"]),
        reason=BUCKET_REASONS[bucket],
        mode_single_model=_single(mission),
        settings=settings,
    )
    return AgentResult(
        agent="data",
        summary=result.text[:600],
        details={"retrieved": hits, "store": "in-memory"},
        routing=result.decision,
    )


async def run_analysis(mission: Mission, prior: list[AgentResult], settings: Settings) -> AgentResult:
    bucket = bucket_for_agent("analysis")
    prior_txt = "\n".join(f"- {r.agent}: {r.summary}" for r in prior)
    result = await complete(
        step="analysis",
        bucket=bucket,
        system="You are the Analysis agent. Produce insights, trade-offs, and a clear recommendation.",
        user=f"Mission: {mission.question}\n\nPrior agent findings:\n{prior_txt}",
        reason=BUCKET_REASONS[bucket],
        mode_single_model=_single(mission),
        settings=settings,
    )
    return AgentResult(agent="analysis", summary=result.text[:800], routing=result.decision)


async def run_synthesizer(mission: Mission, prior: list[AgentResult], settings: Settings) -> AgentResult:
    bucket = bucket_for_agent("synthesizer")
    prior_txt = "\n".join(f"- {r.agent}: {r.summary}" for r in prior)
    result = await complete(
        step="synthesizer",
        bucket=bucket,
        system=(
            "You are OmniForge synthesizer. Write a clear final answer for a principal AI architect. "
            "Structure: Answer → Evidence → Risks → Next steps. Be concise."
        ),
        user=f"Mission: {mission.question}\n\nAgent findings:\n{prior_txt}",
        reason=BUCKET_REASONS[bucket],
        mode_single_model=_single(mission),
        settings=settings,
    )
    return AgentResult(agent="synthesizer", summary=result.text, routing=result.decision)
