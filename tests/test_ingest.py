
import pytest
from omniforge.ingest.normalize import normalize
from omniforge.models import MissionInput, Modality, RouteMode


def test_text_only():
    m = normalize(MissionInput(text="What is multi-LLM routing?"))
    assert Modality.TEXT in m.modalities
    assert "multi-LLM" in m.question


def test_voice_and_text():
    m = normalize(MissionInput(text="Summarize", voice_transcript="hello world"))
    assert Modality.VOICE in m.modalities or Modality.MIXED in m.modalities


def test_requires_input():
    with pytest.raises(ValueError):
        normalize(MissionInput())


def test_war_room_preset():
    m = normalize(MissionInput(text="Acme Corp", preset="war_room"))
    assert "Competitive War Room" in m.question
