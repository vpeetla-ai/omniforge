
"""In-process MCP-style tool bridge (no external MCP server required)."""
from __future__ import annotations

from typing import Any

from omniforge.tools.builtin import TOOL_REGISTRY


async def call_tool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {"error": f"unknown tool: {name}"}
    args = args or {}
    result = fn(args)
    if hasattr(result, "__await__"):
        result = await result  # type: ignore[misc]
    return {"tool": name, "result": result}


def list_tools() -> list[str]:
    return sorted(TOOL_REGISTRY.keys())
