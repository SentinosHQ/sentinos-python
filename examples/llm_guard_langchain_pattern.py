"""LangChain-style tool callback pattern with Sentinos governance gate."""

from __future__ import annotations

from typing import Any, Callable

from sentinos import LLMGuard, SentinosClient


def guarded_tool_call(
    *,
    guard: LLMGuard,
    tool_name: str,
    tool_args: dict[str, Any],
    execute_tool: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    trace = guard.authorize(
        provider="tool-runtime",
        operation="invoke",
        request={"tool": tool_name, "args": tool_args},
        tool_name=f"tool.{tool_name}",
    )
    decision = trace.decision
    if decision not in {"ALLOW", "SHADOW"}:
        return {
            "trace_id": trace.trace_id,
            "decision": decision,
            "reason": trace.policy_evaluation.reason,
        }
    result = execute_tool(**tool_args)
    guard.record_response(
        provider="tool-runtime",
        operation=tool_name,
        trace=trace,
        response=result,
    )
    return {"trace_id": trace.trace_id, "decision": decision, "result": result}


def run_langchain_pattern_example() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="langchain-agent", session_id="sess-004")
    output = guarded_tool_call(
        guard=guard,
        tool_name="stripe.refund",
        tool_args={"amount": 1200, "currency": "USD", "customer_id": "cust-1"},
        execute_tool=lambda **kwargs: {"ok": True, "tool_output": kwargs},
    )
    print(output)


if __name__ == "__main__":
    run_langchain_pattern_example()
