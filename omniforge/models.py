"""Shared Pydantic models for OmniForge missions and routing proof."""
from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    MIXED = "mixed"


class RouteBucket(str, Enum):
    FAST = "fast"
    STRUCTURED = "structured"
    REASONING = "reasoning"
    VISION = "vision"


class RouteMode(str, Enum):
    ROUTED = "routed"
    SINGLE = "single"


class RoutingDecision(BaseModel):
    step: str
    bucket: RouteBucket
    provider: str
    model_id: str
    reason: str
    latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    mocked: bool = False


class AgentResult(BaseModel):
    agent: str
    ok: bool = True
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    routing: RoutingDecision | None = None


class MissionInput(BaseModel):
    text: str | None = None
    image_b64: str | None = None
    image_mime: str | None = "image/png"
    voice_transcript: str | None = None
    preset: str | None = None  # war_room | incident | chart | None
    mode: RouteMode = RouteMode.ROUTED
    single_model: str | None = None


class Mission(BaseModel):
    mission_id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    modalities: list[Modality] = Field(default_factory=list)
    image_caption: str | None = None
    voice_transcript: str | None = None
    preset: str | None = None
    mode: RouteMode = RouteMode.ROUTED
    single_model: str | None = None


class AskResponse(BaseModel):
    mission_id: str
    answer: str
    modalities: list[Modality]
    agents_run: list[str]
    tools_run: list[str]
    waterfall: list[RoutingDecision]
    agent_results: list[AgentResult]
    mode: RouteMode
    total_cost_usd: float
    total_latency_ms: float
    budget_halted: bool = False
    mocked: bool = False
