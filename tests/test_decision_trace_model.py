from datetime import datetime, timezone

from sentinos.models.decision_trace import DecisionTrace


def test_decision_trace_accepts_payment_context() -> None:
    trace = DecisionTrace.model_validate(
        {
            "schema_version": "decision-trace.v1",
            "trace_id": "00000000-0000-0000-0000-000000000014",
            "timestamp": datetime(2026, 5, 8, tzinfo=timezone.utc).isoformat(),
            "tenant_id": "org_123",
            "intent": {
                "type": "payment_authorization",
                "tool": "payment.x402",
                "args": {"protocol": "x402", "amount": "0.25"},
            },
            "payment_context": {
                "protocol": "x402",
                "merchant": "agentic-market-demo",
                "amount": "0.25",
                "asset": "USDC",
                "network": "base-sepolia",
                "budget_window": {"max_usd": "1.00", "expires_in_seconds": 300},
            },
            "policy_evaluation": {
                "policy_id": "seed.agentic.payment",
                "decision": "ALLOW",
            },
        }
    )

    assert trace.payment_context is not None
    assert trace.payment_context.protocol == "x402"
    assert trace.payment_context.merchant == "agentic-market-demo"
    assert trace.payment_context.budget_window == {"max_usd": "1.00", "expires_in_seconds": 300}


def test_decision_trace_accepts_agent_rationale() -> None:
    trace = DecisionTrace.model_validate(
        {
            "schema_version": "decision-trace.v1",
            "trace_id": "00000000-0000-0000-0000-000000000015",
            "timestamp": datetime(2026, 5, 17, tzinfo=timezone.utc).isoformat(),
            "tenant_id": "org_123",
            "intent": {
                "type": "tool_call",
                "tool": "github.create_issue",
                "args": {"repo": "sentinos"},
            },
            "agent_rationale": {
                "schema_version": "agent-rationale.v1",
                "captured_at": datetime(2026, 5, 17, tzinfo=timezone.utc).isoformat(),
                "capture_phase": "pre_execution",
                "capture_mode": "model_supplied",
                "sources": [{"kind": "model", "field_paths": ["metadata.agent_rationale"]}],
                "summary": "Create an auditable remediation item.",
                "goal": "Track a customer-impacting issue.",
                "decision_basis": ["incident confirmed", "repository authorized"],
                "expected_outcome": "Issue created before implementation.",
                "confidence": 0.82,
                "runtime": {"provider": "openai", "model": "gpt-5", "tool": "github.create_issue"},
                "safety": {
                    "hidden_reasoning_dropped": True,
                    "forbidden_fields": ["$.metadata.agent_rationale.hidden_reasoning"],
                },
            },
            "policy_evaluation": {
                "policy_id": "seed.github.issue",
                "decision": "ALLOW",
            },
        }
    )

    assert trace.agent_rationale is not None
    assert trace.agent_rationale.capture_phase == "pre_execution"
    assert trace.agent_rationale.sources[0].kind == "model"
    assert trace.agent_rationale.runtime is not None
    assert trace.agent_rationale.runtime.model == "gpt-5"
    assert trace.agent_rationale.safety is not None
    assert trace.agent_rationale.safety.hidden_reasoning_dropped is True
