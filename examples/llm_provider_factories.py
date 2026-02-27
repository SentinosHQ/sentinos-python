"""Factory-based adapter construction for provider SDK clients."""

from __future__ import annotations

from sentinos import (
    LLMGuard,
    SentinosClient,
    create_anthropic_messages_adapter,
    create_openai_chat_adapter,
)


def run_factory_examples() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="ops-agent", session_id="sess-020")

    # In real usage, omit `client=` and provide api_key/base_url to let factories
    # instantiate provider clients directly (requires optional extras installed).
    openai_adapter = create_openai_chat_adapter(guard=guard, client=fake_openai_client())
    openai_result = openai_adapter.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "summarize active incidents"}],
        temperature=0.2,
    )
    print(openai_result.trace.trace_id, openai_result.trace.decision)

    anthropic_adapter = create_anthropic_messages_adapter(guard=guard, client=fake_anthropic_client())
    anthropic_result = anthropic_adapter.create(
        model="claude-3-5-sonnet",
        messages=[{"role": "user", "content": "draft escalation summary"}],
        max_tokens=256,
    )
    print(anthropic_result.trace.trace_id, anthropic_result.trace.decision)


class _FakeOpenAIChatCompletions:
    @staticmethod
    def create(**kwargs):
        return {"id": "openai-factory", **kwargs}


class _FakeOpenAIChat:
    completions = _FakeOpenAIChatCompletions()


class _FakeOpenAIClient:
    chat = _FakeOpenAIChat()


def fake_openai_client() -> _FakeOpenAIClient:
    return _FakeOpenAIClient()


class _FakeAnthropicMessages:
    @staticmethod
    def create(**kwargs):
        return {"id": "anthropic-factory", **kwargs}


class _FakeAnthropicClient:
    messages = _FakeAnthropicMessages()


def fake_anthropic_client() -> _FakeAnthropicClient:
    return _FakeAnthropicClient()


if __name__ == "__main__":
    run_factory_examples()
