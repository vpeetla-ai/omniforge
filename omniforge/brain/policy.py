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
    "verifier": RouteBucket.REASONING,
    "critic": RouteBucket.REASONING,
}

# App-local names → thesis roles (aegis-routing-contract maps; duplicated for zero-dep mock)
AGENT_THESIS_ROLES: dict[str, str] = {
    "planner": "planner",
    "web": "retriever",
    "api": "executor",
    "data": "retriever",
    "analysis": "executor",
    "vision": "executor",
    "synthesizer": "summarizer",
    "mcp_tool": "executor",
    "verifier": "verifier",
    "critic": "verifier",
}

BUCKET_TO_TIER: dict[RouteBucket, str] = {
    RouteBucket.FAST: "fast",
    RouteBucket.STRUCTURED: "specialized",
    RouteBucket.REASONING: "high_reasoning",
    RouteBucket.VISION: "specialized",
}

BUCKET_REASONS: dict[RouteBucket, str] = {
    RouteBucket.FAST: "Low-latency summarize / classify — prefer cheap free-tier models",
    RouteBucket.STRUCTURED: "JSON / tool contracts — prefer schema-reliable models",
    RouteBucket.REASONING: "Deep analysis / final answer — prefer strongest available",
    RouteBucket.VISION: "Image / screenshot understanding — vision-capable model",
}


def bucket_for_agent(agent: str) -> RouteBucket:
    return AGENT_BUCKETS.get(agent.lower(), RouteBucket.REASONING)


def thesis_role_for_agent(agent: str) -> str:
    return AGENT_THESIS_ROLES.get(agent.lower(), "executor")


def tier_for_bucket(bucket: RouteBucket) -> str:
    return BUCKET_TO_TIER.get(bucket, "high_reasoning")
