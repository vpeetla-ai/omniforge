"""Provider cascade: live keys → next provider → mock. Never lie about mock."""
from __future__ import annotations

import time
from dataclasses import dataclass

from omniforge.config import Settings, get_settings
from omniforge.brain.policy import thesis_role_for_agent, tier_for_bucket
from omniforge.models import RouteBucket, RoutingDecision


@dataclass
class LLMResult:
    text: str
    decision: RoutingDecision


# Rough public list prices (USD / 1M tokens) for local FinOps — illustrative
_PRICE = {
    "mock": (0.0, 0.0),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-haiku": (0.80, 4.0),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-flash": (0.075, 0.30),
}


def estimate_cost(model_id: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = _PRICE.get(model_id, (1.0, 3.0))
    return (tokens_in * pin + tokens_out * pout) / 1_000_000


def llm_gateway_enabled(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return bool((settings.llm_gateway_url or "").strip())


def _cascade_for(bucket: RouteBucket, settings: Settings) -> list[tuple[str, str]]:
    """Ordered (provider, model_id) candidates."""
    if bucket == RouteBucket.FAST:
        out: list[tuple[str, str]] = []
        if settings.groq_api_key:
            out.append(("groq", settings.omniforge_fast_model))
        if settings.google_api_key:
            out.append(("google", settings.omniforge_google_model))
        if settings.openai_api_key:
            out.append(("openai", "gpt-4o-mini"))
        out.append(("mock", "mock"))
        return out
    if bucket == RouteBucket.STRUCTURED:
        out = []
        if settings.openai_api_key:
            out.append(("openai", settings.omniforge_structured_model))
        if settings.google_api_key:
            out.append(("google", settings.omniforge_google_model))
        if settings.anthropic_api_key:
            out.append(("anthropic", "claude-haiku"))
        out.append(("mock", "mock"))
        return out
    if bucket == RouteBucket.VISION:
        out = []
        if settings.openai_api_key:
            out.append(("openai", settings.omniforge_vision_model))
        if settings.google_api_key:
            out.append(("google", settings.omniforge_google_model))
        if settings.anthropic_api_key:
            out.append(("anthropic", "claude-sonnet-4-20250514"))
        out.append(("mock", "mock"))
        return out
    # reasoning
    out = []
    if settings.anthropic_api_key:
        out.append(("anthropic", settings.omniforge_reasoning_model))
    if settings.openai_api_key:
        out.append(("openai", "gpt-4o"))
    if settings.google_api_key:
        out.append(("google", settings.omniforge_google_model))
    if settings.groq_api_key:
        out.append(("groq", settings.omniforge_fast_model))
    out.append(("mock", "mock"))
    return out


def _mock_complete(step: str, system: str, user: str, bucket: RouteBucket) -> str:
    preview = user.strip().replace("\n", " ")[:180]
    return (
        f"[mock:{bucket.value}] {step}: Based on the mission context — {preview}… "
        f"This is a deterministic OmniForge mock response so demos work without API keys."
    )


async def complete(
    *,
    step: str,
    bucket: RouteBucket,
    system: str,
    user: str,
    reason: str,
    mode_single_model: str | None = None,
    image_b64: str | None = None,
    settings: Settings | None = None,
    data_class: str = "internal",
    generator_provider: str | None = None,
    workflow_id: str | None = None,
) -> LLMResult:
    settings = settings or get_settings()
    t0 = time.perf_counter()

    if mode_single_model:
        if mode_single_model == "mock" or not settings.live:
            text = _mock_complete(step, system, user, bucket)
            mocked, provider, model_id = True, "mock", "mock"
        else:
            text, mocked, provider, model_id = await _try_providers(
                [
                    ("openai", mode_single_model),
                    ("anthropic", mode_single_model),
                    ("google", mode_single_model),
                    ("groq", mode_single_model),
                ],
                system,
                user,
                image_b64,
                settings,
                step,
                bucket,
                data_class=data_class,
                generator_provider=generator_provider,
                workflow_id=workflow_id,
            )
    else:
        candidates = _cascade_for(bucket, settings)
        if not settings.live:
            candidates = [("mock", "mock")]
        elif llm_gateway_enabled(settings):
            # Plane-connected: try gateway first, then in-repo provider cascade.
            model_for_bucket = {
                RouteBucket.FAST: settings.omniforge_fast_model,
                RouteBucket.STRUCTURED: settings.omniforge_structured_model,
                RouteBucket.REASONING: settings.omniforge_reasoning_model,
                RouteBucket.VISION: settings.omniforge_vision_model,
            }.get(bucket, "stub-small")
            candidates = [("gateway", model_for_bucket), *candidates]
        text, mocked, provider, model_id = await _try_providers(
            candidates, system, user, image_b64, settings, step, bucket,
            data_class=data_class, generator_provider=generator_provider,
            workflow_id=workflow_id,
        )

    latency = (time.perf_counter() - t0) * 1000
    tin, tout = max(1, len(system + user) // 4), max(1, len(text) // 4)
    decision = RoutingDecision(
        step=step,
        bucket=bucket,
        provider=provider,
        model_id=model_id,
        reason=reason,
        latency_ms=round(latency, 2),
        tokens_in=tin,
        tokens_out=tout,
        cost_usd=round(estimate_cost(model_id, tin, tout), 6),
        mocked=mocked,
        thesis_role=thesis_role_for_agent(step),
        model_tier=tier_for_bucket(bucket),
        data_class=data_class,
        generator_provider=generator_provider,
    )
    return LLMResult(text=text, decision=decision)


async def _try_providers(candidates, system, user, image_b64, settings, step, bucket, data_class='internal', generator_provider=None, workflow_id=None):
    errors: list[str] = []
    for provider, model_id in candidates:
        if provider == "mock" or model_id == "mock":
            return _mock_complete(step, system, user, bucket), True, "mock", "mock"
        try:
            if provider == "gateway" and llm_gateway_enabled(settings):
                text = await _gateway(
                    settings, model_id, system, user, image_b64,
                    step=step, bucket=bucket, data_class=data_class,
                    generator_provider=generator_provider, workflow_id=workflow_id,
                )
                return text, False, "aegis-llm-gateway", model_id
            if provider == "openai" and settings.openai_api_key:
                text = await _openai(settings, model_id, system, user, image_b64)
                return text, False, provider, model_id
            if provider == "anthropic" and settings.anthropic_api_key:
                text = await _anthropic(settings, model_id, system, user, image_b64)
                return text, False, provider, model_id
            if provider == "google" and settings.google_api_key:
                text = await _google(settings, model_id, system, user, image_b64)
                return text, False, provider, model_id
            if provider == "groq" and settings.groq_api_key:
                text = await _groq(settings, model_id, system, user)
                return text, False, provider, model_id
        except Exception as exc:  # noqa: BLE001 — cascade to next provider
            errors.append(f"{provider}:{type(exc).__name__}")
            continue
    text = _mock_complete(step, system, user, bucket)
    if errors:
        text = f"{text}\n\n[cascade misses: {', '.join(errors)}]"
    return text, True, "mock", "mock"


async def _gateway(settings, model_id, system, user, image_b64, *, step="analysis",
                   bucket=None, data_class="internal", generator_provider=None, workflow_id=None):
    """OpenAI-compatible completions via aegis-llm-gateway (optional plane connection)."""
    from openai import AsyncOpenAI
    from omniforge.brain.policy import thesis_role_for_agent, tier_for_bucket
    from omniforge.models import RouteBucket as RB

    bucket = bucket or RB.REASONING
    thesis = thesis_role_for_agent(step)
    # Verifier must use a different selected provider than the generator (ADR-029).
    selected = "gemini" if thesis == "verifier" else "stub"
    if thesis == "verifier" and (generator_provider or "").lower() == "gemini":
        selected = "groq"
    headers = {
        "X-Tenant-Id": settings.llm_gateway_tenant_id or "omniforge",
        "X-Agent-Role": step,
        "X-Thesis-Role": thesis,
        "X-Data-Class": data_class,
        "X-Selected-Provider": selected,
        "X-Model-Tier": tier_for_bucket(bucket),
    }
    if workflow_id:
        headers["X-Workflow-Id"] = workflow_id
    if generator_provider:
        headers["X-Generator-Provider"] = generator_provider
    if thesis == "verifier":
        headers["X-Cache-Bypass"] = "true"

    client = AsyncOpenAI(
        api_key=settings.llm_gateway_api_key or "omniforge-gateway",
        base_url=settings.llm_gateway_url.rstrip("/"),
        default_headers=headers,
    )
    content: list | str
    if image_b64:
        content = [
            {"type": "text", "text": user},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
            },
        ]
    else:
        content = user
    resp = await client.chat.completions.create(
        model=model_id or "stub-small",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content or ""


async def _openai(settings, model_id, system, user, image_b64):
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    content: list | str
    if image_b64:
        content = [
            {"type": "text", "text": user},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
            },
        ]
    else:
        content = user
    resp = await client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content or ""


async def _anthropic(settings, model_id, system, user, image_b64):
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    content: list | str
    if image_b64:
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
            },
            {"type": "text", "text": user},
        ]
    else:
        content = user
    resp = await client.messages.create(
        model=model_id,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    return resp.content[0].text


async def _groq(settings, model_id, system, user):
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
    resp = await client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=1200,
    )
    return resp.choices[0].message.content or ""


async def _google(settings, model_id, system, user, image_b64):
    """Gemini generateContent via REST — no extra SDK required."""
    import httpx

    model = model_id or settings.omniforge_google_model
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={settings.google_api_key}"
    )
    parts: list[dict] = [{"text": f"{system}\n\n{user}"}]
    if image_b64:
        parts.append({"inline_data": {"mime_type": "image/png", "data": image_b64}})
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"maxOutputTokens": 1200},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("google: empty candidates")
    parts_out = candidates[0].get("content", {}).get("parts") or []
    texts = [p.get("text", "") for p in parts_out if p.get("text")]
    if not texts:
        raise RuntimeError("google: empty text")
    return "\n".join(texts)
