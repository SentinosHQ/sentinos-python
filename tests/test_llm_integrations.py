from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest

from sentinos.integrations import (
    LLMGuard,
    LLMPolicyDeniedError,
    LLMPolicyEscalationError,
    guard_openai_chat_completion,
)
from sentinos.models.decision_trace import DecisionTrace


def _trace(decision: str) -> DecisionTrace:
    return DecisionTrace.model_validate(
        {
            "trace_id": "trace-1",
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
    decisions: list[str] = field(default_factory=lambda: ["ALLOW"])
    execute_calls: list[dict[str, Any]] = field(default_factory=list)
    append_calls: list[dict[str, Any]] = field(default_factory=list)

    def execute(self, **kwargs: Any) -> DecisionTrace:
        self.execute_calls.append(kwargs)
        decision = self.decisions.pop(0) if self.decisions else "ALLOW"
        return _trace(decision)

    async def execute_async(self, **kwargs: Any) -> DecisionTrace:
        self.execute_calls.append(kwargs)
        decision = self.decisions.pop(0) if self.decisions else "ALLOW"
        return _trace(decision)

    def append_session_event(self, **kwargs: Any) -> dict[str, Any]:
        self.append_calls.append(kwargs)
        return {"ok": True}

    async def append_session_event_async(self, **kwargs: Any) -> dict[str, Any]:
        self.append_calls.append(kwargs)
        return {"ok": True}


def test_authorize_sets_skip_connector_metadata() -> None:
    kernel = FakeKernel()
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    trace = guard.authorize(
        provider="openai",
        operation="chat.completions",
        model="gpt-4o-mini",
        request={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert trace.decision == "ALLOW"
    call = kernel.execute_calls[0]
    assert call["metadata"]["skip_connector"] is True
    assert call["intent"]["tool"] == "llm.openai.chat.completions"


def test_run_allow_executes_provider_and_records_event() -> None:
    kernel = FakeKernel(decisions=["ALLOW"])
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    ran = {"called": False}

    def invoke() -> dict[str, Any]:
        ran["called"] = True
        return {"id": "resp-1", "model": "gpt-4o-mini", "usage": {"total_tokens": 10}}

    result = guard.run(
        provider="openai",
        operation="chat.completions",
        model="gpt-4o-mini",
        request={"messages": [{"role": "user", "content": "hello"}]},
        invoke=invoke,
    )

    assert ran["called"] is True
    assert result.trace.decision == "ALLOW"
    assert result.response["id"] == "resp-1"
    assert kernel.append_calls and kernel.append_calls[0]["event_type"] == "llm.response"


def test_run_deny_raises() -> None:
    kernel = FakeKernel(decisions=["DENY"])
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    with pytest.raises(LLMPolicyDeniedError):
        guard.run(
            provider="openai",
            operation="chat.completions",
            model="gpt-4o-mini",
            request={"messages": [{"role": "user", "content": "hello"}]},
            invoke=lambda: {"id": "should-not-run"},
        )


def test_run_escalate_raises() -> None:
    kernel = FakeKernel(decisions=["ESCALATE"])
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    with pytest.raises(LLMPolicyEscalationError):
        guard.run(
            provider="openai",
            operation="chat.completions",
            model="gpt-4o-mini",
            request={"messages": [{"role": "user", "content": "hello"}]},
            invoke=lambda: {"id": "should-not-run"},
        )


def test_guard_openai_chat_completion_helper() -> None:
    kernel = FakeKernel(decisions=["ALLOW"])
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    def fake_create(*, model: str, messages: list[dict[str, Any]], temperature: float) -> dict[str, Any]:
        return {"id": "r-1", "model": model, "messages_count": len(messages), "temperature": temperature}

    result = guard_openai_chat_completion(
        guard=guard,
        create=fake_create,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.3,
    )
    assert result.response["id"] == "r-1"
    assert kernel.execute_calls[0]["intent"]["tool"] == "llm.openai.chat.completions"


def test_run_async_allow() -> None:
    kernel = FakeKernel(decisions=["ALLOW"])
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    async def invoke_async() -> dict[str, Any]:
        return {"id": "async-1", "model": "claude-3-5"}

    result = asyncio.run(
        guard.run_async(
            provider="anthropic",
            operation="messages.create",
            model="claude-3-5-sonnet",
            request={"messages": [{"role": "user", "content": "hello"}]},
            invoke=invoke_async,
        )
    )
    assert result.response["id"] == "async-1"
    assert kernel.append_calls and kernel.append_calls[0]["event_type"] == "llm.response"


def test_authorized_call_context_manager() -> None:
    kernel = FakeKernel(decisions=["ALLOW"])
    guard = LLMGuard(kernel=kernel, agent_id="agent-1", session_id="sess-1", tenant_id="acme")

    with guard.authorized_call(
        provider="openai",
        operation="chat.completions",
        model="gpt-4o-mini",
        request={"messages": [{"role": "user", "content": "hello"}]},
    ) as trace:
        response = {"id": "resp-ctx", "model": "gpt-4o-mini"}
        guard.record_response(provider="openai", operation="chat.completions", trace=trace, response=response)

    assert kernel.append_calls and kernel.append_calls[0]["payload"]["summary"]["id"] == "resp-ctx"
