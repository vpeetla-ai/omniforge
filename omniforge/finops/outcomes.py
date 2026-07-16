"""Record compliant outcomes to agent-finops (ADR-029 cost-per-compliant-outcome)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from omniforge.config import Settings
from omniforge.models import AskResponse

logger = logging.getLogger(__name__)


def evaluate_ask_outcome(resp: AskResponse) -> dict[str, Any]:
    """Lightweight golden gate for OmniForge asks (no external suite required)."""
    answer_ok = bool((resp.answer or "").strip()) and len(resp.answer.strip()) >= 20
    has_waterfall = len(resp.waterfall) >= 1
    # Verifier independence soft check when a verifier/critic step exists
    providers = {d.provider for d in resp.waterfall}
    verifier_steps = [d for d in resp.waterfall if (d.thesis_role or "") == "verifier"]
    verifier_ok = True
    if verifier_steps:
        gen_providers = {
            d.provider
            for d in resp.waterfall
            if (d.thesis_role or "") not in {"verifier", None} or d.step not in {"verifier", "critic"}
        }
        # If only one provider overall, still pass in mock mode (gateway may be stub)
        if not resp.mocked and len(providers) < 2 and verifier_steps:
            verifier_ok = False
    eval_pass = answer_ok and has_waterfall and verifier_ok and not resp.budget_halted
    return {
        "eval_pass": eval_pass,
        "policy_deny": False,
        "hitl_required": False,
        "hitl_approved": True,
        "budget_ok": not resp.budget_halted,
        "checks": {
            "answer_ok": answer_ok,
            "has_waterfall": has_waterfall,
            "verifier_ok": verifier_ok,
            "budget_ok": not resp.budget_halted,
        },
    }


async def record_ask_outcome(resp: AskResponse, settings: Settings) -> dict[str, Any] | None:
    base = (settings.agentfinops_url or "").strip()
    if not base:
        return None
    checks = evaluate_ask_outcome(resp)
    payload = {
        "workflow_id": resp.mission_id,
        "tenant_id": settings.llm_gateway_tenant_id or "omniforge",
        "eval_pass": checks["eval_pass"],
        "policy_deny": checks["policy_deny"],
        "hitl_required": checks["hitl_required"],
        "hitl_approved": checks["hitl_approved"],
        "budget_ok": checks["budget_ok"],
        "total_cost_usd": float(resp.total_cost_usd or 0),
    }
    url = base.rstrip("/") + "/v1/outcomes"
    headers = {"Content-Type": "application/json"}
    if settings.agentfinops_api_key:
        headers["X-API-Key"] = settings.agentfinops_api_key
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            data["_checks"] = checks["checks"]
            return data
    except Exception as exc:  # noqa: BLE001 — never fail the ask on FinOps KPI
        logger.warning("finops_outcome_record_failed: %s", exc)
        return {"error": str(exc), "payload": payload, "_checks": checks["checks"]}
