
"""LangGraph-style ask pipeline (explicit async fan-out; works with or without langgraph)."""
from __future__ import annotations

import asyncio
import time

from omniforge.agents import runners
from omniforge.config import Settings, get_settings
from omniforge.finops.ledger import BudgetLedger
from omniforge.finops.outcomes import record_ask_outcome
from omniforge.ingest.normalize import normalize
from omniforge.mcp.bridge import call_tool
from omniforge.models import AskResponse, MissionInput, RouteMode, RoutingDecision
from omniforge.plan.planner import plan_agents, plan_tools


async def run_ask(inp: MissionInput, settings: Settings | None = None) -> AskResponse:
    settings = settings or get_settings()
    t0 = time.perf_counter()
    mission = normalize(inp)
    ledger = BudgetLedger(settings.omniforge_budget_usd)

    agents = plan_agents(mission)
    tools = plan_tools(mission)

    waterfall: list[RoutingDecision] = []
    results = []

    # Tools first (cheap, parallel)
    tool_outputs = []
    for name in tools:
        args = {}
        if name == "mcp_echo":
            args = {"message": mission.question[:120]}
        if name == "mcp_calc":
            args = {"expression": "2+2"}
        out = await call_tool(name, args)
        tool_outputs.append(out)

    # Vision first if needed (feeds caption)
    if "vision" in agents:
        vr = await runners.run_vision(mission, inp.image_b64, settings)
        results.append(vr)
        if vr.routing:
            waterfall.append(vr.routing)
            ledger.record(vr.routing)

    if ledger.halted:
        return _halted(mission, agents, tools, waterfall, results, t0, ledger)

    # Parallel mid agents
    mid = [a for a in agents if a in {"web", "api", "data"}]
    tasks = []
    for a in mid:
        if a == "web":
            tasks.append(runners.run_web(mission, settings))
        elif a == "api":
            tasks.append(runners.run_api(mission, settings))
        elif a == "data":
            tasks.append(runners.run_data(mission, settings))
    mid_results = await asyncio.gather(*tasks)
    for r in mid_results:
        results.append(r)
        if r.routing:
            waterfall.append(r.routing)
            ledger.record(r.routing)

    if ledger.halted:
        return _halted(mission, agents, tools, waterfall, results, t0, ledger)

    if "analysis" in agents:
        ar = await runners.run_analysis(mission, results, settings)
        results.append(ar)
        if ar.routing:
            waterfall.append(ar.routing)
            ledger.record(ar.routing)

    synth = await runners.run_synthesizer(mission, results, settings)
    results.append(synth)
    if synth.routing:
        waterfall.append(synth.routing)
        ledger.record(synth.routing)

    total_ms = (time.perf_counter() - t0) * 1000
    mocked = any(d.mocked for d in waterfall) or settings.omniforge_mode == "mock"
    resp = AskResponse(
        mission_id=mission.mission_id,
        answer=synth.summary,
        modalities=mission.modalities,
        agents_run=agents + ["synthesizer"],
        tools_run=tools,
        waterfall=waterfall,
        agent_results=results,
        mode=mission.mode,
        total_cost_usd=round(ledger.spent, 6),
        total_latency_ms=round(total_ms, 2),
        budget_halted=ledger.halted,
        mocked=mocked,
    )
    await record_ask_outcome(resp, settings)
    return resp


def _halted(mission, agents, tools, waterfall, results, t0, ledger):
    total_ms = (time.perf_counter() - t0) * 1000
    return AskResponse(
        mission_id=mission.mission_id,
        answer="Budget halt: per-ask FinOps envelope exceeded. Raise OMNIFORGE_BUDGET_USD or use mock mode.",
        modalities=mission.modalities,
        agents_run=agents,
        tools_run=tools,
        waterfall=waterfall,
        agent_results=results,
        mode=mission.mode,
        total_cost_usd=round(ledger.spent, 6),
        total_latency_ms=round(total_ms, 2),
        budget_halted=True,
        mocked=True,
    )


async def run_ab(inp: MissionInput, settings: Settings | None = None) -> dict:
    """Run same mission in routed + single(mock) modes for proof."""
    settings = settings or get_settings()
    routed = inp.model_copy(deep=True)
    routed.mode = RouteMode.ROUTED
    single = inp.model_copy(deep=True)
    single.mode = RouteMode.SINGLE
    single.single_model = single.single_model or "mock"
    a, b = await asyncio.gather(run_ask(routed, settings), run_ask(single, settings))
    return {
        "routed": a.model_dump(),
        "single": b.model_dump(),
        "delta": {
            "cost_usd": round(a.total_cost_usd - b.total_cost_usd, 6),
            "latency_ms": round(a.total_latency_ms - b.total_latency_ms, 2),
            "models_routed": sorted({d.model_id for d in a.waterfall}),
            "models_single": sorted({d.model_id for d in b.waterfall}),
        },
    }
