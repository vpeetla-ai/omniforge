
"""Optional Langfuse-style span recording (no-op without keys)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from omniforge.config import Settings


@contextmanager
def mission_span(settings: Settings, name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
    span: dict[str, Any] = {"name": name, **attrs, "events": []}
    try:
        yield span
    finally:
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            # Soft integration point — avoid hard dependency; log attrs for demo
            span["exported"] = False
