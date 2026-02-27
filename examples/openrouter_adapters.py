"""OpenRouter governance examples using Sentinos provider adapters."""

from __future__ import annotations

from sentinos import (
    LLMGuard,
    SentinosClient,
    create_openrouter_chat_adapter,
    create_openrouter_openresponses_adapter,
    create_openrouter_responses_adapter,
)


class _FakeOpenAIChatCompletions:
    @staticmethod
    def create(**kwargs):
        return {"id": "openrouter-chat", **kwargs}


class _FakeOpenAIResponses:
    @staticmethod
    def create(**kwargs):
        return {"id": "openrouter-responses", "status": "completed", **kwargs}


class _FakeOpenAIChat:
    completions = _FakeOpenAIChatCompletions()


class _FakeOpenAIClient:
    chat = _FakeOpenAIChat()
    responses = _FakeOpenAIResponses()


def run_openrouter_examples() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="ops-agent", session_id="sess-openrouter-1")

    openrouter_chat = create_openrouter_chat_adapter(
        guard=guard,
        client=_FakeOpenAIClient(),
    )
    chat_result = openrouter_chat.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "summarize incidents"}],
    )
    print(chat_result.trace.trace_id, chat_result.trace.decision, chat_result.response["id"])

    openrouter_responses = create_openrouter_responses_adapter(
        guard=guard,
        client=_FakeOpenAIClient(),
    )
    responses_result = openrouter_responses.create(
        model="openai/gpt-4.1-mini",
        input=[{"role": "user", "content": "draft runbook"}],
    )
    print(responses_result.trace.trace_id, responses_result.trace.decision, responses_result.response["id"])

    openrouter_openresponses = create_openrouter_openresponses_adapter(
        guard=guard,
        client=_FakeOpenAIClient(),
    )
    openresponses_result = openrouter_openresponses.create(
        model="openai/gpt-4.1-mini",
        input=[{"type": "message", "role": "user", "content": "create status summary"}],
    )
    print(openresponses_result.trace.trace_id, openresponses_result.trace.decision, openresponses_result.response.id)


if __name__ == "__main__":
    run_openrouter_examples()
