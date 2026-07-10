
"""In-repo side-effect gate — no AegisAI dependency."""
from __future__ import annotations

from dataclasses import dataclass

from omniforge.config import Settings


@dataclass
class GateDecision:
    allowed: bool
    reason: str


def authorize_export(settings: Settings, action: str = "export") -> GateDecision:
    """Demo fail-open unless PRODUCTION_STRICT."""
    if settings.production_strict:
        # Strict profile: require explicit approval token in future; deny by default for export
        return GateDecision(False, "PRODUCTION_STRICT denies export without HITL approval")
    if settings.omniforge_gateway_fail_open:
        return GateDecision(True, "fail-open demo gate allows export")
    return GateDecision(False, "gateway fail-closed")
