"""Provider-agnostic LLM governance using Sentinos LLMGuard."""

from __future__ import annotations

from sentinos import LLMGuard, SentinosClient


def fake_provider_call(*, model: str, messages: list[dict[str, str]], temperature: float) -> dict[str, object]:
    return {
        "id": "resp-123",
        "model": model,
        "usage": {"prompt_tokens": len(str(messages)), "completion_tokens": 42},
        "temperature": temperature,
    }


def run_any_provider_example() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="support-agent", session_id="sess-001")

    result = guard.run(
        provider="openai",
        operation="chat.completions",
        model="gpt-4o-mini",
        request={
            "messages": [
                {"role": "system", "content": "You are concise and safe."},
                {"role": "user", "content": "Summarize yesterday's incident."},
            ]
        },
        invoke=lambda: fake_provider_call(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Summarize yesterday's incident."}],
            temperature=0.2,
        ),
    )
    print(result.trace.trace_id, result.trace.decision, result.response["id"])


if __name__ == "__main__":
    run_any_provider_example()
