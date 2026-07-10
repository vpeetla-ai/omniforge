# ADR-001: Self-contained multimodal multi-LLM platform

## Status
Accepted

## Context
Leaders need one inspectable product that answers text/image/voice asks with multi-agent fan-out and multi-LLM routing — without wiring half the org at demo time.

## Decision
OmniForge is a monorepo that owns ingest, planner, agents, MCP tools, Multi-LLM Brain, RAG, FinOps ledger, and policy gate. Task-class routing (`fast` / `structured` / `reasoning` / `vision`) with provider cascades. No required sibling-repo HTTP dependencies.

## Consequences
- Duplicates some org patterns (intentional)
- Demo works on mock with zero paid keys
- Live mode unlocks Groq / OpenAI / Anthropic when keys exist
