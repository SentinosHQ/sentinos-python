from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest

from sentinos.integrations import (
    AsyncOpenResponsesAdapter,
    LLMGuard,
    LLMPolicyDeniedError,
    OpenResponsesAdapter,
    create_async_openresponses_adapter,
    create_async_openrouter_openresponses_adapter,
    create_openresponses_adapter,
    create_openrouter_openresponses_adapter,
    guard_openresponses_create,
    iter_openresponses_sse_lines,
    parse_openresponses_sse_event,
)
from sentinos.models.decision_trace import DecisionTrace


def _trace(decision: str) -> DecisionTrace:
    return DecisionTrace.model_validate(
        {
            "trace_id": "trace-openresponses-1",
            "timestamp": "2026-02-07T00:00:00Z",
            "tenant_id": "acme",
            "agent_id": "agent-1",
            "session_id": "sess-1",
            "intent": {"type": "llm_call", "tool": "llm.openresponses.responses.create", "args": {}},
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


def test_guard_openresponses_create_helper() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    result = guard_openresponses_create(
        guard=guard,
        create=lambda **kwargs: {"id": "resp-1", "status": "completed", **kwargs},
        model="gpt-4.1-mini",
        input=[{"type": "message", "role": "user", "content": "hello"}],
    )
    assert result.response.id == "resp-1"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openresponses.responses.create"


def test_openresponses_adapter_create_and_request() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = OpenResponsesAdapter(
        guard=guard,
        create_fn=lambda **kwargs: {"id": "resp-2", "status": "completed", **kwargs},
    )

    result = adapter.create(
        model="gpt-4.1-mini",
        input=[{"type": "message", "role": "user", "content": "summarize"}],
        tools=[{"type": "function", "name": "get_status"}],
        tool_choice="auto",
    )
    assert result.response.id == "resp-2"
    assert result.response.model == "gpt-4.1-mini"

    result_2 = adapter.create_request(
        request={
            "model": "gpt-4.1-mini",
            "input": [{"type": "message", "role": "user", "content": "follow up"}],
            "metadata": {"tenant": "acme"},
        }
    )
    assert result_2.response.status == "completed"


def test_openresponses_stream_collects_events_and_final_response() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    lines = [
        "event: response.created",
        'data: {"type":"response.created","sequence_number":1}',
        "",
        "event: response.completed",
        (
            'data: {"type":"response.completed","sequence_number":2,'
            '"response":{"id":"resp-stream","status":"completed","model":"gpt-4.1-mini","output":[]}}'
        ),
        "",
        "data: [DONE]",
        "",
    ]

    adapter = OpenResponsesAdapter(
        guard=guard,
        create_fn=lambda **kwargs: {"id": "unused", **kwargs},
        stream_fn=lambda **kwargs: lines,
    )
    result = adapter.stream(
        model="gpt-4.1-mini",
        input=[{"type": "message", "role": "user", "content": "hello"}],
    )
    assert result.decision == "ALLOW"
    assert len(result.events) >= 2
    assert result.final_response is not None
    assert result.final_response.id == "resp-stream"
    assert kernel.events and kernel.events[0]["event_type"] == "llm.response"


def test_openresponses_stream_denied_raises() -> None:
    kernel = FakeKernel(decision="DENY")
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    adapter = OpenResponsesAdapter(
        guard=guard,
        create_fn=lambda **kwargs: {"id": "unused", **kwargs},
        stream_fn=lambda **kwargs: [],
    )
    with pytest.raises(LLMPolicyDeniedError):
        adapter.stream(model="gpt-4.1-mini", input=[{"type": "message", "role": "user", "content": "hello"}])


def test_sse_helpers_support_json_lines_and_done() -> None:
    events = list(
        iter_openresponses_sse_lines(
            [
                '{"type":"response.created","sequence_number":1}',
                "",
                "data: [DONE]",
                "",
            ]
        )
    )
    assert events[0].type == "response.created"
    assert events[-1].type == "response.done"

    event = parse_openresponses_sse_event('{"type":"response.failed","sequence_number":9}')
    assert event is not None
    assert event.type == "response.failed"


def test_openresponses_factory_with_explicit_clients() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    class _Responses:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "factory-sync", "status": "completed", **kwargs}

        @staticmethod
        def stream(**kwargs: Any) -> list[dict[str, Any]]:
            return [
                {"type": "response.created", "sequence_number": 1},
                {
                    "type": "response.completed",
                    "sequence_number": 2,
                    "response": {"id": "factory-stream", "status": "completed", **kwargs},
                },
            ]

    class _Client:
        responses = _Responses()

    adapter = create_openresponses_adapter(guard=guard, client=_Client())
    out = adapter.create(model="gpt-4.1-mini", input="hello")
    assert out.response.id == "factory-sync"
    stream_out = adapter.stream(model="gpt-4.1-mini", input="hello")
    assert stream_out.final_response is not None
    assert stream_out.final_response.id == "factory-stream"


def test_async_openresponses_adapter() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    async def create_fn(**kwargs: Any) -> dict[str, Any]:
        return {"id": "async-created", "status": "completed", **kwargs}

    async def stream_fn(**kwargs: Any) -> list[dict[str, Any]]:
        return [
            {"type": "response.created", "sequence_number": 1},
            {
                "type": "response.completed",
                "sequence_number": 2,
                "response": {"id": "async-stream", "status": "completed", **kwargs},
            },
        ]

    adapter = AsyncOpenResponsesAdapter(guard=guard, create_fn=create_fn, stream_fn=stream_fn)
    created = asyncio.run(adapter.create(model="gpt-4.1-mini", input="hello"))
    assert created.response.id == "async-created"

    streamed = asyncio.run(adapter.stream(model="gpt-4.1-mini", input="hello"))
    assert streamed.final_response is not None
    assert streamed.final_response.id == "async-stream"


def test_async_factory_with_explicit_client() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    class _Responses:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "async-factory", "status": "completed", **kwargs}

    class _Client:
        responses = _Responses()

    adapter = create_async_openresponses_adapter(guard=guard, client=_Client())
    out = asyncio.run(adapter.create(model="gpt-4.1-mini", input="hello"))
    assert out.response.id == "async-factory"


def test_openresponses_factory_provider_override() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    class _Responses:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "override-sync", "status": "completed", **kwargs}

    class _Client:
        responses = _Responses()

    adapter = create_openresponses_adapter(
        guard=guard,
        client=_Client(),
        provider="openrouter",
        operation="responses.create",
    )
    out = adapter.create(model="openai/gpt-4.1-mini", input="hello")
    assert out.response.id == "override-sync"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.responses.create"


def test_openrouter_openresponses_factory_defaults_and_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    created_kwargs: dict[str, Any] = {}

    class _Responses:
        @staticmethod
        def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "or-sync", "status": "completed", **kwargs}

    class _AsyncResponses:
        @staticmethod
        async def create(**kwargs: Any) -> dict[str, Any]:
            return {"id": "or-async", "status": "completed", **kwargs}

    class _OpenAIClient:
        responses = _Responses()

        def __init__(self, **kwargs: Any):
            created_kwargs.update(kwargs)

    class _AsyncOpenAIClient:
        responses = _AsyncResponses()

        def __init__(self, **kwargs: Any):
            created_kwargs.update(kwargs)

    class _OpenAIModule:
        OpenAI = _OpenAIClient
        AsyncOpenAI = _AsyncOpenAIClient

    monkeypatch.setattr(
        "sentinos.integrations.openresponses.importlib.import_module",
        lambda name: _OpenAIModule(),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-env-key")

    adapter = create_openrouter_openresponses_adapter(
        guard=guard,
        http_referer="https://console.sentinos.dev",
        x_title="Sentinos Console",
    )
    out = adapter.create(model="openai/gpt-4.1-mini", input="hello")
    assert out.response.id == "or-sync"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.responses.create"
    assert created_kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert created_kwargs["api_key"] == "openrouter-env-key"
    assert created_kwargs["default_headers"]["HTTP-Referer"] == "https://console.sentinos.dev"
    assert created_kwargs["default_headers"]["X-Title"] == "Sentinos Console"

    async_adapter = create_async_openrouter_openresponses_adapter(guard=guard)
    out_async = asyncio.run(async_adapter.create(model="openai/gpt-4.1-mini", input="hello"))
    assert out_async.response.id == "or-async"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.openrouter.responses.create"
