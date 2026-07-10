# Agent Instructions — OmniForge

Read CONTEXT.md. This repo is **self-contained** — do not add runtime deps on other vpeetla-ai services.

- Python 3.11+, FastAPI, Pydantic v2
- `pip install -e ".[dev]"` + `pytest -q` before claiming done
- Side effects go through `omniforge/gateway` + `PRODUCTION_STRICT`
