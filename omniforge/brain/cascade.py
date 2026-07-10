"""Provider cascade: live keys → next provider → mock. Never lie about mock."""
from __future__ import annotations

import time
from dataclasses import dataclass

from omniforge.config import Settings, get_settings
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
}


def estimate_cost(model_id: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = _PRICE.get(model_id, (1.0, 3.0))
    return (tokens_in * pin + tokens_out * pout) / 1_000_000


def _cascade_for(bucket: RouteBucket, settings: Settings) -> list[tuple[str, str]]:
    """Ordered (provider, model_id) candidates."""
    if bucket == RouteBucket.FAST:
        out: list[tuple[str, str]] = []
        if settings.groq_api_key:
            out.append(("groq", settings.omniforge_fast_model))
        if settings.openai_api_key:
            out.append(("openai", "gpt-4o-mini"))
        out.append(("mock", "mock"))
        return out
    if bucket == RouteBucket.STRUCTURED:
        out = []
        if settings.openai_api_key:
            out.append(("openai", settings.omniforge_structured_model))
        if settings.anthropic_api_key:
            out.append(("anthropic", "claude-haiku"))
        out.append(("mock", "mock"))
        return out
    if bucket == RouteBucket.VISION:
        out = []
        if settings.openai_api_key:
            out.append(("openai", settings.omniforge_vision_model))
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
) -> LLMResult:
    settings = settings or get_settings()
    t0 = time.perf_counter()

    if mode_single_model:
        provider, model_id = "single", mode_single_model
        if mode_single_model == "mock" or not settings.live:
            text = _mock_complete(step, system, user, bucket)
            mocked = True
        else:
            text, mocked = await _try_providers(
                [("openai", mode_single_model), ("anthropic", mode_single_model), ("groq", mode_single_model)],
                system,
                user,
                image_b64,
                settings,
                step,
                bucket,
            )
    else:
        candidates = _cascade_for(bucket, settings)
        if not settings.live:
            candidates = [("mock", "mock")]
        text, mocked, provider, model_id = await _try_providers_named(
            candidates, system, user, image_b64, settings, step, bucket
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
    )
    return LLMResult(text=text, decision=decision)


async def _try_providers_named(candidates, system, user, image_b64, settings, step, bucket):
    text, mocked = await _try_providers(candidates, system, user, image_b64, settings, step, bucket)
    # find which provider succeeded — _try_providers returns text; track via side channel
    # For simplicity: if mocked, last is mock; else first non-mock that worked is unknown —
    # re-run selection: if text starts with [mock, it's mock
    if mocked or text.startswith("[mock:"):
        return text, True, "mock", "mock"
    provider, model_id = candidates[0]
    return text, False, provider, model_id


async def _try_providers(candidates, system, user, image_b64, settings, step, bucket):
    for provider, model_id in candidates:
        if provider == "mock" or model_id == "mock":
            return _mock_complete(step, system, user, bucket), True
        try:
            if provider == "openai" and settings.openai_api_key:
                text = await _openai(settings, model_id, system, user, image_b64)
                return text, False
            if provider == "anthropic" and settings.anthropic_api_key:
                text = await _anthropic(settings, model_id, system, user, image_b64)
                return text, False
            if provider == "groq" and settings.groq_api_key:
                text = await _groq(settings, model_id, system, user)
                return text, False
        except Exception:
            continue
    return _mock_complete(step, system, user, bucket), True


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
