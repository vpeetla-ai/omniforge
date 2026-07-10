
"""Normalize text / image / voice into a Mission."""
from __future__ import annotations

from omniforge.models import Mission, MissionInput, Modality


PRESETS = {
    "war_room": (
        "Competitive War Room: Analyze the company/product below. "
        "Cover positioning, recent signals, strengths/risks, and a crisp recommendation."
    ),
    "incident": (
        "Incident desk: From the screenshot/error context below, triage severity, "
        "likely root causes, and immediate next actions."
    ),
    "chart": (
        "Explain the chart/image and extract the key insight a principal architect should care about."
    ),
}


def normalize(inp: MissionInput) -> Mission:
    parts: list[str] = []
    modalities: list[Modality] = []

    if inp.preset and inp.preset in PRESETS:
        parts.append(PRESETS[inp.preset])

    if inp.text and inp.text.strip():
        parts.append(inp.text.strip())
        modalities.append(Modality.TEXT)

    voice = (inp.voice_transcript or "").strip()
    if voice:
        parts.append(f"[voice transcript] {voice}")
        modalities.append(Modality.VOICE)

    image_caption = None
    if inp.image_b64:
        modalities.append(Modality.IMAGE)
        # Caption filled later by vision agent; placeholder for planner
        image_caption = "(image attached — vision agent will describe)"
        parts.append("[image attached]")

    if not parts:
        raise ValueError("Provide text, image, and/or voice_transcript")

    question = "\n\n".join(parts)
    if len(modalities) > 1:
        modalities = [Modality.MIXED, *modalities]

    # dedupe while preserving order
    seen: set[Modality] = set()
    mods: list[Modality] = []
    for m in modalities:
        if m not in seen:
            seen.add(m)
            mods.append(m)

    return Mission(
        question=question,
        modalities=mods or [Modality.TEXT],
        image_caption=image_caption,
        voice_transcript=voice or None,
        preset=inp.preset,
        mode=inp.mode,
        single_model=inp.single_model or ("mock" if inp.mode.value == "single" else None),
    )
