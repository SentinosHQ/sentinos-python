"""OpenAI Agents SDK governed refund tool with a Sentinos decision boundary."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any

try:
    from agents import Agent, ModelSettings, Runner, function_tool
except ModuleNotFoundError as exc:
    raise ImportError(
        "Optional dependency 'openai-agents' is not installed. Install with: pip install 'sentinos[agents]'"
    ) from exc

from sentinos import LLMGuard, SentinosClient, make_guarded_tool


def run_openai_agents_governed_tools_example(
    *,
    client: Any | None = None,
    refund_executor: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    client = client or SentinosClient.from_env(org_id=os.getenv("SENTINOS_ORG_ID"))
    guard = LLMGuard(
        kernel=client.kernel,
        agent_id=os.getenv("SENTINOS_AGENT_ID", "refund-ops-agent"),
        session_id=os.getenv("SENTINOS_SESSION_ID", "sess-python-openai-agents"),
    )

    execute_refund = refund_executor or (
        lambda **kwargs: {
            "id": f"refund_{kwargs['payment_intent']}",
            "status": "submitted",
            "amount": kwargs["amount"],
            "currency": kwargs.get("currency", "USD"),
        }
    )

    governed_refund = make_guarded_tool(
        guard=guard,
        tool_name="refund.execute",
        execute=execute_refund,
    )

    latest_outcome: dict[str, Any] = {}

    @function_tool
    def issue_refund(
        payment_intent: str,
        amount: int,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Submit a refund request through a Sentinos-governed side-effect boundary."""

        result = governed_refund(
            payment_intent=payment_intent,
            amount=amount,
            currency=currency,
        )
        latest_outcome.update(
            {
                "traceId": result["trace_id"],
                "decision": result["decision"],
                "refundId": (result.get("result") or {}).get("id"),
            }
        )
        return result

    agent = Agent(
        name="Refund approvals agent",
        instructions=(
            "Review customer refund requests. When a request clearly asks for a refund and "
            "the payment intent plus amount are present, call issue_refund exactly once."
        ),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        model_settings=ModelSettings(tool_choice="required"),
        tool_use_behavior="stop_on_first_tool",
        tools=[issue_refund],
    )

    run_result = Runner.run_sync(
        agent,
        (
            "Issue a refund for payment intent pi_demo_refund for 1800 cents in USD because "
            "the customer requested a refund."
        ),
    )

    if not latest_outcome:
        raise RuntimeError(
            f"OpenAI Agents example did not produce a governed tool call. Final output: {getattr(run_result, 'final_output', None)!r}"
        )

    return {
        "traceId": latest_outcome["traceId"],
        "decision": latest_outcome["decision"],
        "refundId": latest_outcome.get("refundId"),
        "rationaleMode": "sdk_derived",
        "rationaleSummary": "Authorize tool-runtime.refund.execute before execution.",
        "nextStep": (
            "Open the Sentinos console, search for the traceId in Traces, and inspect the "
            "Agent Rationale for the governed tool call."
        ),
    }


def main() -> None:
    print(json.dumps(run_openai_agents_governed_tools_example(), indent=2))


if __name__ == "__main__":
    main()
