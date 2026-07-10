# OmniForge Architecture

## Problem

Most LLM apps hardcode one model. Multimodal asks need **specialized agents**, **tools**, and **the right model per step** — with proof.

## Decision

Ship a **self-contained** platform: ingest → plan → fan-out → Multi-LLM Brain → synthesize → waterfall. Duplicate FinOps/gateway/RAG/voice pieces in-repo rather than depend on sibling services.

## Components

1. **Ingest** — text, image (vision), voice transcript
2. **Planner** — selects agents + MCP tools
3. **Brain** — `RouteBucket` → provider cascade → `RoutingDecision`
4. **Agents** — web, api, data, analysis, vision, synthesizer
5. **MCP bridge** — in-process tools
6. **Proof** — waterfall, A/B, local FinOps, export gate

## Non-goals

Runtime coupling to VAP, VoiceForge, AegisAI, or agent-finops.
