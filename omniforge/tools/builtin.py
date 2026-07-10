
"""Allowlisted tools — also exposed via in-process MCP bridge."""
from __future__ import annotations

import ast
import operator
from datetime import datetime, timezone
from typing import Any

import httpx

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def tool_time(_: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"utc": datetime.now(timezone.utc).isoformat()}


def tool_echo(args: dict[str, Any]) -> dict[str, Any]:
    return {"echo": args.get("message", "")}


def tool_calc(args: dict[str, Any]) -> dict[str, Any]:
    expr = str(args.get("expression", "0"))
    try:
        value = _safe_eval(expr)
        return {"expression": expr, "value": value}
    except Exception as e:
        return {"expression": expr, "error": str(e)}


async def tool_http_get(args: dict[str, Any]) -> dict[str, Any]:
    url = str(args.get("url", ""))
    # Allowlist: only http(s) and block obvious SSRF locals
    if not url.startswith(("http://", "https://")):
        return {"error": "only http(s) URLs allowed"}
    blocked = ("localhost", "127.0.0.1", "0.0.0.0", "169.254.", "::1")
    if any(b in url for b in blocked):
        return {"error": "blocked host"}
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            r = await client.get(url)
            text = r.text[:2000]
            return {"status": r.status_code, "url": str(r.url), "body_preview": text}
    except Exception as e:
        return {"error": str(e)}


def _safe_eval(expr: str) -> float:
    node = ast.parse(expr, mode="eval")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](_eval(n.operand))
        raise ValueError("unsafe expression")

    return float(_eval(node))


TOOL_REGISTRY = {
    "mcp_time": tool_time,
    "mcp_echo": tool_echo,
    "mcp_calc": tool_calc,
    "mcp_http_get": tool_http_get,
}
