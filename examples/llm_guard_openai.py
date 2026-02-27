"""OpenAI-style completion helper with Sentinos policy guard."""

from __future__ import annotations

from typing import Any

from sentinos import LLMGuard, SentinosClient, guard_openai_chat_completion


def fake_openai_chat_create(*, model: str, messages: list[dict[str, Any]], temperature: float = 0.2) -> dict[str, Any]:
    return {
        "id": "chatcmpl-1",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Acknowledged."}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
        "temperature": temperature,
        "messages_count": len(messages),
    }


def run_openai_example() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="ops-bot", session_id="sess-002")
    result = guard_openai_chat_completion(
        guard=guard,
        create=fake_openai_chat_create,
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a SOC analyst assistant."},
            {"role": "user", "content": "Classify this alert."},
        ],
        temperature=0.1,
    )
    print(result.trace.trace_id, result.response["id"])


if __name__ == "__main__":
    run_openai_example()
