"""Task-class routing policy — agents request buckets, never hardcode models."""
from __future__ import annotations

from omniforge.models import RouteBucket

# Agent / step → default bucket
AGENT_BUCKETS: dict[str, RouteBucket] = {
    "planner": RouteBucket.STRUCTURED,
    "web": RouteBucket.FAST,
    "api": RouteBucket.STRUCTURED,
    "data": RouteBucket.FAST,
    "analysis": RouteBucket.REASONING,
    "vision": RouteBucket.VISION,
    "synthesizer": RouteBucket.REASONING,
    "mcp_tool": RouteBucket.STRUCTURED,
}

BUCKET_REASONS: dict[RouteBucket, str] = {
    RouteBucket.FAST: "Low-latency summarize / classify — prefer cheap free-tier models",
    RouteBucket.STRUCTURED: "JSON / tool contracts — prefer schema-reliable models",
    RouteBucket.REASONING: "Deep analysis / final answer — prefer strongest available",
    RouteBucket.VISION: "Image / screenshot understanding — vision-capable model",
}


def bucket_for_agent(agent: str) -> RouteBucket:
    return AGENT_BUCKETS.get(agent.lower(), RouteBucket.REASONING)
