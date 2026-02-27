"""Drop-in provider adapter class examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos import (
    AnthropicMessagesAdapter,
    LLMGuard,
    OpenAIChatCompletionsAdapter,
    SentinosClient,
    make_guarded_tool,
)


@dataclass
class FakeOpenAIChatCompletions:
    def create(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        return {"id": "chat-1", "model": model, "messages_count": len(messages), **kwargs}


@dataclass
class FakeOpenAIChat:
    completions: FakeOpenAIChatCompletions


@dataclass
class FakeOpenAIClient:
    chat: FakeOpenAIChat


@dataclass
class FakeAnthropicMessages:
    def create(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        return {"id": "msg-1", "model": model, "messages_count": len(messages), **kwargs}


@dataclass
class FakeAnthropicClient:
    messages: FakeAnthropicMessages


def run_adapter_examples() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="runtime-agent", session_id="sess-010")

    openai_client = FakeOpenAIClient(chat=FakeOpenAIChat(completions=FakeOpenAIChatCompletions()))
    openai_adapter = OpenAIChatCompletionsAdapter.from_client(guard=guard, client=openai_client)
    openai_result = openai_adapter.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Summarize incidents."}],
        temperature=0.2,
    )
    print(openai_result.trace.trace_id, openai_result.response["id"])

    anthropic_client = FakeAnthropicClient(messages=FakeAnthropicMessages())
    anthropic_adapter = AnthropicMessagesAdapter.from_client(guard=guard, client=anthropic_client)
    anthropic_result = anthropic_adapter.create(
        model="claude-3-5-sonnet",
        messages=[{"role": "user", "content": "Generate response plan."}],
        max_tokens=256,
    )
    print(anthropic_result.trace.trace_id, anthropic_result.response["id"])

    guarded_refund = make_guarded_tool(
        guard=guard,
        tool_name="stripe.refund",
        execute=lambda **kwargs: {"ok": True, "forwarded": kwargs},
    )
    tool_result = guarded_refund(amount=250, currency="USD", customer_id="cust-77")
    print(tool_result["trace_id"], tool_result["decision"])


if __name__ == "__main__":
    run_adapter_examples()
