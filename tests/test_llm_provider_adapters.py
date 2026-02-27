from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest

from sentinos.integrations import (
    AnthropicMessagesAdapter,
    AsyncAnthropicMessagesAdapter,
    AsyncOpenAIChatCompletionsAdapter,
    AsyncOpenAIResponsesAdapter,
    LLMGuard,
    OpenAIChatCompletionsAdapter,
    OpenAIResponsesAdapter,
    create_anthropic_messages_adapter,
    create_async_anthropic_messages_adapter,
    create_async_openai_chat_adapter,
    create_async_openai_responses_adapter,
    create_async_openrouter_chat_adapter,
    create_async_openrouter_responses_adapter,
    create_openai_chat_adapter,
    create_openai_responses_adapter,
    create_openrouter_chat_adapter,
    create_openrouter_responses_adapter,
    make_guarded_tool,
    make_guarded_tool_async,
)
from sentinos.models.decision_trace import DecisionTrace


def _trace(decision: str) -> DecisionTrace:
    return DecisionTrace.model_validate(
        {
            "trace_id": "trace-provider-1",
            "timestamp": "2026-02-07T00:00:00Z",
            "tenant_id": "acme",
            "agent_id": "agent-1",
            "session_id": "sess-1",
            "intent": {"type": "llm_call", "tool": "llm.openai.chat.completions", "args": {}},
            "policy_evaluation": {
                "policy_id": "llm-guard",
                "policy_version": "v1",
                "decision": decision,
                "reason": "rule-evaluated",
            },
        }
    )


@dataclass
class FakeKernel:
    decision: str = "ALLOW"
    last_execute: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def execute(self, **kwargs: Any) -> DecisionTrace:
        self.last_execute = kwargs
        return _trace(self.decision)

    async def execute_async(self, **kwargs: Any) -> DecisionTrace:
        self.last_execute = kwargs
        return _trace(self.decision)

    def append_session_event(self, **kwargs: Any) -> dict[str, Any]:
        self.events.append(kwargs)
        return {"ok": True}

    async def append_session_event_async(self, **kwargs: Any) -> dict[str, Any]:
        self.events.append(kwargs)
        return {"ok": True}


def test_openai_adapter_create() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = OpenAIChatCompletionsAdapter(
        guard=guard,
        create_fn=lambda **kwargs: {"id": "resp-openai", **kwargs},
    )

    result = adapter.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hello"}], temperature=0.1)
    assert result.response["id"] == "resp-openai"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openai.chat.completions"


def test_anthropic_adapter_create() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = AnthropicMessagesAdapter(
        guard=guard,
        create_fn=lambda **kwargs: {"id": "resp-anthropic", **kwargs},
    )

    result = adapter.create(model="claude-3-5-sonnet", messages=[{"role": "user", "content": "hello"}], max_tokens=200)
    assert result.response["id"] == "resp-anthropic"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.anthropic.messages.create"


def test_async_openai_adapter_create() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    async def create_fn(**kwargs: Any) -> dict[str, Any]:
        return {"id": "resp-async-openai", **kwargs}

    adapter = AsyncOpenAIChatCompletionsAdapter(guard=guard, create_fn=create_fn)
    result = asyncio.run(
        adapter.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hello"}], temperature=0.2)
    )
    assert result.response["id"] == "resp-async-openai"


def test_async_anthropic_adapter_create() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    async def create_fn(**kwargs: Any) -> dict[str, Any]:
        return {"id": "resp-async-anthropic", **kwargs}

    adapter = AsyncAnthropicMessagesAdapter(guard=guard, create_fn=create_fn)
    result = asyncio.run(
        adapter.create(model="claude-3-5-sonnet", messages=[{"role": "user", "content": "hello"}], max_tokens=120)
    )
    assert result.response["id"] == "resp-async-anthropic"


def test_make_guarded_tool() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    wrapped = make_guarded_tool(
        guard=guard,
        tool_name="stripe.refund",
        execute=lambda **kwargs: {"ok": True, "args": kwargs},
    )
    out = wrapped(amount=100, currency="USD")
    assert out["decision"] == "ALLOW"
    assert out["result"]["ok"] is True


def test_make_guarded_tool_async() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    async def execute_async(**kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "args": kwargs}

    wrapped = make_guarded_tool_async(
        guard=guard,
        tool_name="stripe.refund",
        execute=execute_async,
    )
    out = asyncio.run(wrapped(amount=100, currency="USD"))
    assert out["decision"] == "ALLOW"
    assert out["result"]["ok"] is True


def test_openai_responses_adapter_create() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = OpenAIResponsesAdapter(
        guard=guard,
        create_fn=lambda **kwargs: {"id": "resp-openai-resp", **kwargs},
    )
    result = adapter.create(model="gpt-4.1-mini", input=[{"role": "user", "content": "hello"}])
    assert result.response["id"] == "resp-openai-resp"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openai.responses.create"


def test_async_openai_responses_adapter_create() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    async def create_fn(**kwargs: Any) -> dict[str, Any]:
        return {"id": "resp-async-openai-resp", **kwargs}

    adapter = AsyncOpenAIResponsesAdapter(guard=guard, create_fn=create_fn)
    result = asyncio.run(adapter.create(model="gpt-4.1-mini", input=[{"role": "user", "content": "hello"}]))
    assert result.response["id"] == "resp-async-openai-resp"


def test_factory_functions_with_explicit_clients() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    class _OpenAIChatCompletions:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "openai-chat", **kwargs}

    class _OpenAIResponses:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "openai-responses", **kwargs}

    class _OpenAIChat:
        completions = _OpenAIChatCompletions()

    class _OpenAIClient:
        chat = _OpenAIChat()
        responses = _OpenAIResponses()

    class _AsyncOpenAIChatCompletions:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "async-openai-chat", **kwargs}

    class _AsyncOpenAIResponses:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "async-openai-responses", **kwargs}

    class _AsyncOpenAIChat:
        completions = _AsyncOpenAIChatCompletions()

    class _AsyncOpenAIClient:
        chat = _AsyncOpenAIChat()
        responses = _AsyncOpenAIResponses()

    class _AnthropicMessages:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "anthropic-msg", **kwargs}

    class _AnthropicClient:
        messages = _AnthropicMessages()

    class _AsyncAnthropicMessages:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "async-anthropic-msg", **kwargs}

    class _AsyncAnthropicClient:
        messages = _AsyncAnthropicMessages()

    openai_adapter = create_openai_chat_adapter(guard=guard, client=_OpenAIClient())
    openai_result = openai_adapter.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert openai_result.response["id"] == "openai-chat"

    openai_resp_adapter = create_openai_responses_adapter(guard=guard, client=_OpenAIClient())
    assert openai_resp_adapter.create(model="gpt-4.1-mini", input="hello").response["id"] == "openai-responses"

    async_openai_adapter = create_async_openai_chat_adapter(guard=guard, client=_AsyncOpenAIClient())
    got = asyncio.run(async_openai_adapter.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}]))
    assert got.response["id"] == "async-openai-chat"

    async_openai_resp_adapter = create_async_openai_responses_adapter(guard=guard, client=_AsyncOpenAIClient())
    got = asyncio.run(async_openai_resp_adapter.create(model="gpt-4.1-mini", input="hello"))
    assert got.response["id"] == "async-openai-responses"

    anthropic_adapter = create_anthropic_messages_adapter(guard=guard, client=_AnthropicClient())
    anthropic_result = anthropic_adapter.create(
        model="claude-3-5-sonnet",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert anthropic_result.response["id"] == "anthropic-msg"

    async_anthropic_adapter = create_async_anthropic_messages_adapter(guard=guard, client=_AsyncAnthropicClient())
    got = asyncio.run(
        async_anthropic_adapter.create(model="claude-3-5-sonnet", messages=[{"role": "user", "content": "hi"}])
    )
    assert got.response["id"] == "async-anthropic-msg"


def test_openrouter_chat_factory_uses_openrouter_provider_and_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    created_kwargs: dict[str, Any] = {}

    class _OpenAIChatCompletions:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "openrouter-chat", **kwargs}

    class _OpenAIChat:
        completions = _OpenAIChatCompletions()

    class _OpenAIClient:
        chat = _OpenAIChat()

        def __init__(self, **kwargs: Any):
            created_kwargs.update(kwargs)

    class _OpenAIModule:
        OpenAI = _OpenAIClient
        AsyncOpenAI = _OpenAIClient

    monkeypatch.setattr(
        "sentinos.integrations.providers.importlib.import_module",
        lambda name: _OpenAIModule(),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-openrouter-key")

    adapter = create_openrouter_chat_adapter(
        guard=guard,
        http_referer="https://console.sentinos.dev",
        x_title="Sentinos Console",
    )
    out = adapter.create(model="openai/gpt-4.1-mini", messages=[{"role": "user", "content": "hello"}])
    assert out.response["id"] == "openrouter-chat"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.chat.completions"
    assert created_kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert created_kwargs["api_key"] == "env-openrouter-key"
    assert created_kwargs["default_headers"]["HTTP-Referer"] == "https://console.sentinos.dev"
    assert created_kwargs["default_headers"]["X-Title"] == "Sentinos Console"


def test_openrouter_responses_factories_use_openrouter_provider() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    class _Responses:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "openrouter-responses", **kwargs}

    class _Client:
        responses = _Responses()

    class _AsyncResponses:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "openrouter-responses-async", **kwargs}

    class _AsyncClient:
        responses = _AsyncResponses()

    adapter = create_openrouter_responses_adapter(guard=guard, client=_Client())
    out = adapter.create(model="openai/gpt-4.1-mini", input="hello")
    assert out.response["id"] == "openrouter-responses"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.responses.create"

    async_adapter = create_async_openrouter_responses_adapter(guard=guard, client=_AsyncClient())
    out_async = asyncio.run(async_adapter.create(model="openai/gpt-4.1-mini", input="hello"))
    assert out_async.response["id"] == "openrouter-responses-async"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.responses.create"


def test_async_openrouter_chat_factory_with_explicit_client() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    class _ChatCompletions:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "openrouter-chat-async", **kwargs}

    class _Chat:
        completions = _ChatCompletions()

    class _Client:
        chat = _Chat()

    adapter = create_async_openrouter_chat_adapter(guard=guard, client=_Client())
    out = asyncio.run(adapter.create(model="openai/gpt-4.1-mini", messages=[{"role": "user", "content": "hi"}]))
    assert out.response["id"] == "openrouter-chat-async"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.chat.completions"


def test_factory_missing_dependency_message(monkeypatch: pytest.MonkeyPatch) -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    def raise_missing(name: str) -> Any:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("sentinos.integrations.providers.importlib.import_module", raise_missing)

    with pytest.raises(ImportError, match="pip install 'sentinos\\[openai\\]'"):
        create_openai_chat_adapter(guard=guard)

    with pytest.raises(ImportError, match="pip install 'sentinos\\[anthropic\\]'"):
        create_anthropic_messages_adapter(guard=guard)
