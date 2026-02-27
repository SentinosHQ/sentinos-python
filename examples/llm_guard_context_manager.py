"""Context-manager style policy gate around an external LLM call."""

from __future__ import annotations

from typing import Any

from sentinos import LLMGuard, SentinosClient


def fake_anthropic_messages_create(*, model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "msg-1",
        "model": model,
        "content": [{"type": "text", "text": "Investigation plan drafted."}],
        "messages_count": len(messages),
    }


def run_context_manager_example() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="response-agent", session_id="sess-003")

    with guard.authorized_call(
        provider="anthropic",
        operation="messages.create",
        model="claude-3-5-sonnet",
        request={"messages": [{"role": "user", "content": "Draft response plan for this incident."}]},
    ) as trace:
        response = fake_anthropic_messages_create(
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "Draft response plan for this incident."}],
        )
        guard.record_response(
            provider="anthropic",
            operation="messages.create",
            trace=trace,
            response=response,
        )
        print(trace.trace_id, response["id"])


if __name__ == "__main__":
    run_context_manager_example()
