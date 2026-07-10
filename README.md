# OmniForge


<!-- vpeetla-tech-stack:start -->
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square)]() [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square)]() [![LangGraph](https://img.shields.io/badge/LangGraph-style-9333EA?style=flat-square)]() [![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square)]() [![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square)]() [![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square)]()
<!-- vpeetla-tech-stack:end -->

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Ask anything. Right agents. Right models.**

Self-contained **multimodal multi-agent multi-LLM** answer platform — text, image/screenshot, and voice fan out across specialized agents and MCP tools, with a live **model waterfall** proving which model ran each step.

> **Self-contained:** no runtime dependency on other vpeetla-ai services. FinOps ledger, policy gate, RAG, voice ingest, and MCP bridge all live in this monorepo.

## Architecture

Canonical: [`docs/diagrams/canonical-architecture.mmd`](docs/diagrams/canonical-architecture.mmd)

```mermaid
flowchart TB
  Text["Text"] --> Norm["Normalize"]
  Image["Image"] --> Vision["Vision Agent"]
  Voice["Voice ASR"] --> Norm
  Vision --> Norm
  Norm --> Plan["Planner"]
  Plan --> Fan["Parallel agents + MCP tools"]
  Fan --> Brain["Multi-LLM Brain"]
  Brain --> Synth["Synthesizer"]
  Brain --> Waterfall["RoutingDecision waterfall"]
  Synth --> UI["Answer + proof"]
```

## Honest status

| Component | Status | Notes |
|-----------|--------|-------|
| Multimodal ingest (text / image / voice transcript) | ✅ | Browser ASR supplies transcript; optional Whisper later |
| Planner fan-out | ✅ | Selects vision/web/api/data/analysis + MCP tools |
| Multi-LLM Brain (task-class buckets) | ✅ | fast / structured / reasoning / vision cascades |
| Provider cascade (Groq / OpenAI / Anthropic / mock) | ✅ | Missing keys fall through; mock never claimed as live |
| Parallel agents + synthesizer | ✅ | Async gather mid-agents |
| In-process MCP tool bridge | ✅ | time, echo, calc, allowlisted http_get |
| In-memory RAG | ✅ | Qdrant URL optional (not required) |
| In-repo FinOps budget halt | ✅ | `OMNIFORGE_BUDGET_USD` |
| In-repo export gate + `PRODUCTION_STRICT` | ✅ | No AegisAI dependency |
| A/B single vs routed | ✅ | `POST /v1/ask/ab` |
| Next.js Ask workbench | ✅ | Waterfall + multimodal input |
| Live paid providers on Render | 🟡 | Set keys + `OMNIFORGE_MODE=live` |
| Server Whisper ASR / edge-tts | 🟡 | Browser path ships; server optional |
| External MCP servers | ⬜ | In-process bridge first |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,api]"
pytest -q
uvicorn api.main:app --reload --port 8080
```

```bash
curl -s http://localhost:8080/health
curl -s -X POST http://localhost:8080/v1/ask \
  -H 'content-type: application/json' \
  -d '{"text":"What is task-class multi-LLM routing?","preset":"war_room"}'
```

UI:

```bash
cd ui && npm install && npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8080`.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /v1/ops/metrics` | Providers, tools, budget |
| `POST /v1/ask` | Multimodal ask → answer + waterfall |
| `POST /v1/ask/ab` | Routed vs single-model compare |
| `POST /v1/export` | Side-effect gate (strict denies) |

## Deploy

| Layer | Host | URL |
|-------|------|-----|
| API | Render | https://omniforge-api.onrender.com |
| UI | Vercel (`ui/`, static export) | set Root Directory = `ui`, Output = `out`, Framework = Other |

**Vercel manual settings:** Root Directory `ui` · Framework Preset **Other** · Build `npm run build` · Output `out` · Env `NEXT_PUBLIC_API_URL=https://omniforge-api.onrender.com`

See [docs/DEPLOY.md](docs/DEPLOY.md). Do not use the default Next.js serverless preset with this static export.

## Docs

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [ADR-001](docs/adr/ADR-001-omniforge-self-contained-multimodal-multi-llm.md)
- [DEPLOY.md](docs/DEPLOY.md)

Built by [vpeetla-ai](https://github.com/vpeetla-ai) — [venkat-ai.com](https://venkat-ai.com)
