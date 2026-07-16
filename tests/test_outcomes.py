import respx
from httpx import Response

from omniforge.config import Settings
from omniforge.finops.outcomes import evaluate_ask_outcome, record_ask_outcome
from omniforge.models import AskResponse, Modality, RouteBucket, RouteMode, RoutingDecision


def _resp(**kwargs) -> AskResponse:
    base = dict(
        mission_id="m1",
        answer="A sufficiently long OmniForge answer for the golden gate to pass.",
        modalities=[Modality.TEXT],
        agents_run=["web", "synthesizer"],
        tools_run=[],
        waterfall=[
            RoutingDecision(
                step="web",
                bucket=RouteBucket.FAST,
                provider="groq",
                model_id="llama",
                reason="fast",
                thesis_role="retriever",
                model_tier="fast",
            ),
            RoutingDecision(
                step="synthesizer",
                bucket=RouteBucket.REASONING,
                provider="anthropic",
                model_id="claude",
                reason="reasoning",
                thesis_role="summarizer",
                model_tier="high_reasoning",
            ),
        ],
        agent_results=[],
        mode=RouteMode.ROUTED,
        total_cost_usd=0.11,
        total_latency_ms=12.0,
        budget_halted=False,
        mocked=False,
    )
    base.update(kwargs)
    return AskResponse(**base)


def test_evaluate_ask_outcome_pass():
    checks = evaluate_ask_outcome(_resp())
    assert checks["eval_pass"] is True
    assert checks["budget_ok"] is True


def test_evaluate_ask_outcome_budget_halt():
    checks = evaluate_ask_outcome(_resp(budget_halted=True, answer="halt"))
    assert checks["eval_pass"] is False
    assert checks["budget_ok"] is False


@respx.mock
async def test_record_ask_outcome_posts():
    settings = Settings(agentfinops_url="http://finops.test", agentfinops_api_key="k")
    route = respx.post("http://finops.test/v1/outcomes").mock(
        return_value=Response(200, json={"compliant_success": True, "workflow_id": "m1"})
    )
    out = await record_ask_outcome(_resp(), settings)
    assert route.called
    assert out is not None
    assert out.get("compliant_success") is True
