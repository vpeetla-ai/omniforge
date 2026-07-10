
"""Planner selects which agents/tools to run for a mission."""
from __future__ import annotations

from omniforge.models import Mission, Modality


def plan_agents(mission: Mission) -> list[str]:
    """Return ordered agent names to execute (parallel where graph allows)."""
    q = mission.question.lower()
    agents: list[str] = []

    has_image = Modality.IMAGE in mission.modalities or Modality.MIXED in mission.modalities
    if has_image or mission.image_caption:
        agents.append("vision")

    # Always gather context for non-trivial asks
    agents.extend(["web", "api", "data"])

    # Heuristic extras
    if any(k in q for k in ("incident", "error", "stack", "traceback", "outage")):
        if "vision" not in agents:
            agents.insert(0, "vision")
    if any(k in q for k in ("compete", "war room", "competitor", "market")):
        pass  # web/api/data already cover

    agents.append("analysis")
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for a in agents:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def plan_tools(mission: Mission) -> list[str]:
    q = mission.question.lower()
    tools = ["mcp_time", "mcp_echo"]
    if any(k in q for k in ("http", "url", "fetch", "api")):
        tools.append("mcp_http_get")
    if any(k in q for k in ("calc", "compute", "%", "roi")):
        tools.append("mcp_calc")
    return tools
