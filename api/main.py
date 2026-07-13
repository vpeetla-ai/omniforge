
"""OmniForge FastAPI — self-contained multimodal Ask API."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from omniforge.config import get_settings
from omniforge.gateway.policy import authorize_export
from omniforge.graph.ask import run_ab, run_ask
from omniforge.mcp.bridge import list_tools
from omniforge.models import AskResponse, MissionInput, RouteMode

settings = get_settings()
app = FastAPI(title="OmniForge", version="0.1.0", description="Ask anything. Right agents. Right models.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    text: str | None = None
    image_b64: str | None = None
    image_mime: str | None = "image/png"
    voice_transcript: str | None = None
    preset: str | None = Field(default=None, description="war_room | incident | chart")
    mode: RouteMode = RouteMode.ROUTED
    single_model: str | None = None


class ExportRequest(BaseModel):
    mission_id: str
    answer: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "omniforge",
        "mode": settings.omniforge_mode,
        "production_strict": settings.production_strict,
    }


@app.get("/v1/ops/metrics")
def metrics():
    s = get_settings()
    gateway_on = bool((s.llm_gateway_url or "").strip())
    return {
        "service": "omniforge",
        "mode": s.omniforge_mode,
        "providers": {
            "openai": bool(s.openai_api_key),
            "anthropic": bool(s.anthropic_api_key),
            "groq": bool(s.groq_api_key),
            "google": bool(s.google_api_key),
        },
        "budget_usd": s.omniforge_budget_usd,
        "tools": list_tools(),
        "qdrant_configured": bool(s.qdrant_url),
        "langfuse_configured": bool(s.langfuse_public_key),
        "extra": {
            "llm_gateway": {
                "enabled": gateway_on,
                "url_configured": gateway_on,
                "tenant_id": s.llm_gateway_tenant_id if gateway_on else None,
                "plane": "aegis-llm-gateway",
            }
        },
    }


@app.post("/v1/ask", response_model=AskResponse)
async def ask(body: AskRequest):
    try:
        inp = MissionInput(**body.model_dump())
        return await run_ask(inp, settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/ask/ab")
async def ask_ab(body: AskRequest):
    try:
        inp = MissionInput(**body.model_dump())
        return await run_ab(inp, settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/export")
def export(body: ExportRequest):
    decision = authorize_export(settings)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    return {"ok": True, "mission_id": body.mission_id, "gate": decision.reason}
