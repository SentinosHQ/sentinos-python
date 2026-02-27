from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest

from sentinos.integrations import (
    AsyncBedrockConverseAdapter,
    BedrockAccessDeniedError,
    BedrockConverseAdapter,
    BedrockProviderError,
    BedrockThrottlingError,
    BedrockValidationError,
    LLMGuard,
    LLMPolicyDeniedError,
    create_async_bedrock_converse_adapter,
    create_bedrock_converse_adapter,
)
from sentinos.models.decision_trace import DecisionTrace


class _FakeClientError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


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


class FakeBedrockClient:
    def __init__(self, *, error_code: str | None = None):
        self.error_code = error_code
        self.last_converse_payload: dict[str, Any] | None = None
        self.last_stream_payload: dict[str, Any] | None = None
        self.converse_calls = 0
        self.stream_calls = 0

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.converse_calls += 1
        self.last_converse_payload = dict(kwargs)
        if self.error_code is not None:
            raise _FakeClientError(self.error_code, f"provider failure {self.error_code}")
        return {
            "output": {"message": {"content": [{"text": "Bedrock sync output"}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 9, "outputTokens": 4, "totalTokens": 13},
            "metrics": {"latencyMs": 42},
        }

    def converse_stream(self, **kwargs: Any) -> dict[str, Any]:
        self.stream_calls += 1
        self.last_stream_payload = dict(kwargs)
        if self.error_code is not None:
            raise _FakeClientError(self.error_code, f"provider failure {self.error_code}")
        return {
            "stream": iter(
                [
                    {"contentBlockDelta": {"delta": {"text": "Hello "}}},
                    {"contentBlockDelta": {"delta": {"text": "world"}}},
                    {"messageStop": {"stopReason": "end_turn"}},
                    {"metadata": {"usage": {"inputTokens": 5, "outputTokens": 2}, "metrics": {"latencyMs": 21}}},
                ]
            )
        }


def _trace(decision: str) -> DecisionTrace:
    return DecisionTrace.model_validate(
        {
            "trace_id": "trace-bedrock-1",
            "timestamp": "2026-02-07T00:00:00Z",
            "tenant_id": "acme",
            "agent_id": "agent-1",
            "session_id": "sess-1",
            "intent": {"type": "llm_call", "tool": "llm.bedrock.converse", "args": {}},
            "policy_evaluation": {
                "policy_id": "llm-guard",
                "policy_version": "v1",
                "decision": decision,
                "reason": "rule-evaluated",
            },
        }
    )


def test_bedrock_converse_payload_and_response_recording() -> None:
    kernel = FakeKernel()
    client = FakeBedrockClient()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = BedrockConverseAdapter(guard=guard, client=client)

    result = adapter.converse(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=[{"role": "user", "content": [{"text": "hello"}]}],
        system=[{"text": "You are concise."}],
        inference_config={"temperature": 0.2},
        tool_config={"tools": []},
        guardrail_config={"guardrailIdentifier": "gr-1"},
        additional_model_request_fields={"top_k": 10},
        additional_model_response_field_paths=["$.output_text"],
        request_metadata={"workflow": "incident"},
        performance_config={"latency": "optimized"},
        prompt_variables={"customer": "acme"},
    )

    assert result.response["stopReason"] == "end_turn"
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.bedrock.converse"
    assert client.last_converse_payload is not None
    assert client.last_converse_payload["modelId"] == "anthropic.claude-3-5-sonnet-20240620-v1:0"
    assert client.last_converse_payload["inferenceConfig"] == {"temperature": 0.2}
    assert client.last_converse_payload["toolConfig"] == {"tools": []}
    assert client.last_converse_payload["guardrailConfig"] == {"guardrailIdentifier": "gr-1"}
    assert client.last_converse_payload["additionalModelRequestFields"] == {"top_k": 10}
    assert client.last_converse_payload["additionalModelResponseFieldPaths"] == ["$.output_text"]
    assert client.last_converse_payload["requestMetadata"] == {"workflow": "incident"}
    assert client.last_converse_payload["performanceConfig"] == {"latency": "optimized"}
    assert client.last_converse_payload["promptVariables"] == {"customer": "acme"}
    assert kernel.events and kernel.events[0]["event_type"] == "llm.response"


def test_bedrock_stream_collects_events_and_output() -> None:
    kernel = FakeKernel()
    client = FakeBedrockClient()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = BedrockConverseAdapter(guard=guard, client=client)

    result = adapter.converse_stream(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=[{"role": "user", "content": [{"text": "hello"}]}],
    )

    assert result.decision == "ALLOW"
    assert result.output_text == "Hello world"
    assert result.stop_reason == "end_turn"
    assert result.usage == {"inputTokens": 5, "outputTokens": 2}
    assert result.metrics == {"latencyMs": 21}
    assert len(result.events) == 4
    assert kernel.last_execute is not None
    assert kernel.last_execute["intent"]["tool"] == "llm.bedrock.converse_stream"
    assert kernel.events and kernel.events[0]["event_type"] == "llm.response"


def test_bedrock_stream_denied_does_not_call_provider() -> None:
    kernel = FakeKernel(decision="DENY")
    client = FakeBedrockClient()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = BedrockConverseAdapter(guard=guard, client=client)

    with pytest.raises(LLMPolicyDeniedError):
        adapter.converse_stream(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )

    assert client.stream_calls == 0


@pytest.mark.parametrize(
    ("error_code", "expected"),
    [
        ("AccessDeniedException", BedrockAccessDeniedError),
        ("ThrottlingException", BedrockThrottlingError),
        ("ValidationException", BedrockValidationError),
        ("InternalServerException", BedrockProviderError),
    ],
)
def test_bedrock_error_mapping(error_code: str, expected: type[Exception]) -> None:
    kernel = FakeKernel()
    client = FakeBedrockClient(error_code=error_code)
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = BedrockConverseAdapter(guard=guard, client=client)

    with pytest.raises(expected):
        adapter.converse(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )


def test_async_bedrock_adapter_converse_and_stream() -> None:
    kernel = FakeKernel()
    client = FakeBedrockClient()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")
    adapter = AsyncBedrockConverseAdapter(guard=guard, client=client)

    converse_result = asyncio.run(
        adapter.converse(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )
    )
    assert converse_result.response["stopReason"] == "end_turn"

    stream_result = asyncio.run(
        adapter.converse_stream(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            messages=[{"role": "user", "content": [{"text": "hello"}]}],
        )
    )
    assert stream_result.output_text == "Hello world"
    assert stream_result.stop_reason == "end_turn"


def test_bedrock_factories_with_explicit_client() -> None:
    kernel = FakeKernel()
    client = FakeBedrockClient()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    adapter = create_bedrock_converse_adapter(guard=guard, client=client)
    assert isinstance(adapter, BedrockConverseAdapter)

    async_adapter = create_async_bedrock_converse_adapter(guard=guard, client=client)
    assert isinstance(async_adapter, AsyncBedrockConverseAdapter)


def test_bedrock_factory_missing_dependency_message(monkeypatch: pytest.MonkeyPatch) -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    def raise_missing(name: str) -> Any:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("sentinos.integrations.bedrock.importlib.import_module", raise_missing)

    with pytest.raises(ImportError, match="pip install 'sentinos\\[bedrock\\]'"):
        create_bedrock_converse_adapter(guard=guard)
