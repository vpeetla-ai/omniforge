# OmniForge — share copy (LinkedIn / social)

## One-liner

**OmniForge** — Ask anything (text, image, voice). Right agents. Right models. With a live waterfall that proves which LLM ran each step.

## Short post

```
I shipped OmniForge — a self-contained multimodal multi-agent multi-LLM platform.

❌ Don't hardcode one model
✅ Route by task class (fast / structured / reasoning / vision)
✅ Fan out across agents + MCP tools
✅ Prove it with a model waterfall + A/B compare

Live demo → https://omniforge-flame.vercel.app
API → https://omniforge-api.onrender.com/health
Architecture → https://github.com/vpeetla-ai/omniforge/blob/main/docs/ARCHITECTURE.md
ADR-027 → https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-027-omniforge-self-contained-multimodal-multi-llm.md

Stack: LangGraph-style fan-out · FastAPI · Next.js · Groq/OpenAI/Anthropic/Gemini cascades · in-repo FinOps + export gate
No sibling-repo runtime deps — one monorepo you can inspect end-to-end.
```

## 60-second demo script

1. Open the live UI
2. Pick **War Room** (or free-form)
3. Ask a real question; optionally attach a screenshot or use Voice
4. Click **Ask** — watch agents run
5. Scroll to **Model waterfall** — different buckets/providers per step
6. Optional: **Compare A/B** (routed vs single)

## Honesty notes for comments

- Free-tier Render cold start ~30s on first hit after idle
- If keys missing or cascade fails, UI shows **mock fallback** (never claims live)
- `omniforge.vercel.app` may require disabling Vercel Deployment Protection; public URL today: **omniforge-flame.vercel.app**
