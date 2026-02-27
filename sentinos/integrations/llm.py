from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ..kernel import KernelClient
from ..models.decision_trace import DecisionTrace

T = TypeVar("T")


class LLMPolicyExecutionError(RuntimeError):
    """Base error raised when policy does not allow external LLM execution."""

    def __init__(self, message: str, *, trace: DecisionTrace):
        super().__init__(message)
        self.trace = trace


class LLMPolicyDeniedError(LLMPolicyExecutionError):
    """Raised when Sentinos returns DENY for a governed LLM/provider call."""


class LLMPolicyEscalationError(LLMPolicyExecutionError):
    """Raised when Sentinos returns ESCALATE for a governed LLM/provider call."""


@dataclass(frozen=True)
class LLMPolicyResult(Generic[T]):
    provider: str
    operation: str
    trace: DecisionTrace
    response: T


def _tool_name(provider: str, operation: str) -> str:
    p = provider.strip().lower()
    op = operation.strip().lower()
    if not p:
        raise ValueError("provider is required")
    if not op:
        raise ValueError("operation is required")
    return f"llm.{p}.{op}"


def _decision_text(trace: DecisionTrace) -> str:
    return str(trace.decision).strip().upper()


def _summarize_response(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        summary: dict[str, Any] = {}
        for key in ("id", "model", "created", "usage", "stop_reason", "type"):
            if key in response:
                summary[key] = response[key]
        if summary:
            return summary
    return {"response_type": type(response).__name__}


@dataclass
class LLMGuard:
    """
    Provider-agnostic runtime guard for external LLM/provider calls.

    Pattern:
    1) authorize via Kernel (`skip_connector=true`)
    2) execute provider call in your app only when decision is ALLOW/SHADOW
    3) optionally append response summary to session event log
    """

    kernel: KernelClient
    agent_id: str
    session_id: str
    tenant_id: str | None = None

    def _merged_metadata(
        self,
        *,
        provider: str,
        operation: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {
            "skip_connector": True,
            "integration_kind": "llm",
            "provider": provider,
            "operation": operation,
        }
        if metadata:
            merged.update(metadata)
        return merged

    def authorize(
        self,
        *,
        provider: str,
        operation: str,
        request: dict[str, Any],
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        tool_name: str | None = None,
    ) -> DecisionTrace:
        tool = tool_name or _tool_name(provider, operation)
        intent_args: dict[str, Any] = {
            "provider": provider,
            "operation": operation,
            "request": request,
        }
        if model is not None:
            intent_args["model"] = model
        return self.kernel.execute(
            agent_id=self.agent_id,
            session_id=self.session_id,
            intent={"type": "llm_call", "tool": tool, "args": intent_args},
            metadata=self._merged_metadata(provider=provider, operation=operation, metadata=metadata),
            tenant_id=(tenant_id or self.tenant_id),
        )

    async def authorize_async(
        self,
        *,
        provider: str,
        operation: str,
        request: dict[str, Any],
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        tool_name: str | None = None,
    ) -> DecisionTrace:
        tool = tool_name or _tool_name(provider, operation)
        intent_args: dict[str, Any] = {
            "provider": provider,
            "operation": operation,
            "request": request,
        }
        if model is not None:
            intent_args["model"] = model
        return await self.kernel.execute_async(
            agent_id=self.agent_id,
            session_id=self.session_id,
            intent={"type": "llm_call", "tool": tool, "args": intent_args},
            metadata=self._merged_metadata(provider=provider, operation=operation, metadata=metadata),
            tenant_id=(tenant_id or self.tenant_id),
        )

    def run(
        self,
        *,
        provider: str,
        operation: str,
        request: dict[str, Any],
        invoke: Callable[[], T],
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        tool_name: str | None = None,
        response_summarizer: Callable[[T], dict[str, Any]] | None = None,
    ) -> LLMPolicyResult[T]:
        trace = self.authorize(
            provider=provider,
            operation=operation,
            request=request,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            tool_name=tool_name,
        )
        decision = _decision_text(trace)
        if decision == "DENY":
            raise LLMPolicyDeniedError(
                f"Sentinos denied {provider}.{operation}: {trace.policy_evaluation.reason or 'policy denied'}",
                trace=trace,
            )
        if decision == "ESCALATE":
            raise LLMPolicyEscalationError(
                f"Sentinos escalated {provider}.{operation}: {trace.policy_evaluation.reason or 'approval required'}",
                trace=trace,
            )

        response = invoke()
        summarizer = response_summarizer or _summarize_response
        try:
            self.kernel.append_session_event(
                session_id=self.session_id,
                event_type="llm.response",
                payload={
                    "provider": provider,
                    "operation": operation,
                    "decision": decision,
                    "trace_id": trace.trace_id,
                    "summary": summarizer(response),
                },
                tenant_id=(tenant_id or self.tenant_id),
            )
        except Exception:
            # Event capture is best-effort; policy trace is already persisted.
            pass

        return LLMPolicyResult(provider=provider, operation=operation, trace=trace, response=response)

    def record_response(
        self,
        *,
        provider: str,
        operation: str,
        trace: DecisionTrace,
        response: Any,
        tenant_id: str | None = None,
        response_summarizer: Callable[[Any], dict[str, Any]] | None = None,
    ) -> None:
        summarizer = response_summarizer or _summarize_response
        self.kernel.append_session_event(
            session_id=self.session_id,
            event_type="llm.response",
            payload={
                "provider": provider,
                "operation": operation,
                "decision": _decision_text(trace),
                "trace_id": trace.trace_id,
                "summary": summarizer(response),
            },
            tenant_id=(tenant_id or self.tenant_id),
        )

    @contextmanager
    def authorized_call(
        self,
        *,
        provider: str,
        operation: str,
        request: dict[str, Any],
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        tool_name: str | None = None,
    ) -> Iterator[DecisionTrace]:
        trace = self.authorize(
            provider=provider,
            operation=operation,
            request=request,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            tool_name=tool_name,
        )
        decision = _decision_text(trace)
        if decision == "DENY":
            raise LLMPolicyDeniedError(
                f"Sentinos denied {provider}.{operation}: {trace.policy_evaluation.reason or 'policy denied'}",
                trace=trace,
            )
        if decision == "ESCALATE":
            raise LLMPolicyEscalationError(
                f"Sentinos escalated {provider}.{operation}: {trace.policy_evaluation.reason or 'approval required'}",
                trace=trace,
            )
        yield trace

    async def run_async(
        self,
        *,
        provider: str,
        operation: str,
        request: dict[str, Any],
        invoke: Callable[[], Awaitable[T]],
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        tool_name: str | None = None,
        response_summarizer: Callable[[T], dict[str, Any]] | None = None,
    ) -> LLMPolicyResult[T]:
        trace = await self.authorize_async(
            provider=provider,
            operation=operation,
            request=request,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            tool_name=tool_name,
        )
        decision = _decision_text(trace)
        if decision == "DENY":
            raise LLMPolicyDeniedError(
                f"Sentinos denied {provider}.{operation}: {trace.policy_evaluation.reason or 'policy denied'}",
                trace=trace,
            )
        if decision == "ESCALATE":
            raise LLMPolicyEscalationError(
                f"Sentinos escalated {provider}.{operation}: {trace.policy_evaluation.reason or 'approval required'}",
                trace=trace,
            )

        response = await invoke()
        summarizer = response_summarizer or _summarize_response
        try:
            await self.kernel.append_session_event_async(
                session_id=self.session_id,
                event_type="llm.response",
                payload={
                    "provider": provider,
                    "operation": operation,
                    "decision": decision,
                    "trace_id": trace.trace_id,
                    "summary": summarizer(response),
                },
                tenant_id=(tenant_id or self.tenant_id),
            )
        except Exception:
            # Event capture is best-effort; policy trace is already persisted.
            pass

        return LLMPolicyResult(provider=provider, operation=operation, trace=trace, response=response)

    async def record_response_async(
        self,
        *,
        provider: str,
        operation: str,
        trace: DecisionTrace,
        response: Any,
        tenant_id: str | None = None,
        response_summarizer: Callable[[Any], dict[str, Any]] | None = None,
    ) -> None:
        summarizer = response_summarizer or _summarize_response
        await self.kernel.append_session_event_async(
            session_id=self.session_id,
            event_type="llm.response",
            payload={
                "provider": provider,
                "operation": operation,
                "decision": _decision_text(trace),
                "trace_id": trace.trace_id,
                "summary": summarizer(response),
            },
            tenant_id=(tenant_id or self.tenant_id),
        )

    @asynccontextmanager
    async def authorized_call_async(
        self,
        *,
        provider: str,
        operation: str,
        request: dict[str, Any],
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        tool_name: str | None = None,
    ) -> AsyncIterator[DecisionTrace]:
        trace = await self.authorize_async(
            provider=provider,
            operation=operation,
            request=request,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            tool_name=tool_name,
        )
        decision = _decision_text(trace)
        if decision == "DENY":
            raise LLMPolicyDeniedError(
                f"Sentinos denied {provider}.{operation}: {trace.policy_evaluation.reason or 'policy denied'}",
                trace=trace,
            )
        if decision == "ESCALATE":
            raise LLMPolicyEscalationError(
                f"Sentinos escalated {provider}.{operation}: {trace.policy_evaluation.reason or 'approval required'}",
                trace=trace,
            )
        yield trace


def guard_openai_chat_completion(
    *,
    guard: LLMGuard,
    create: Callable[..., T],
    model: str,
    messages: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    **kwargs: Any,
) -> LLMPolicyResult[T]:
    request_payload: dict[str, Any] = {"model": model, "messages": messages}
    if kwargs:
        request_payload["params"] = kwargs
    return guard.run(
        provider="openai",
        operation="chat.completions",
        request=request_payload,
        model=model,
        metadata=metadata,
        tenant_id=tenant_id,
        invoke=lambda: create(model=model, messages=messages, **kwargs),
    )


def guard_anthropic_messages(
    *,
    guard: LLMGuard,
    create: Callable[..., T],
    model: str,
    messages: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    **kwargs: Any,
) -> LLMPolicyResult[T]:
    request_payload: dict[str, Any] = {"model": model, "messages": messages}
    if kwargs:
        request_payload["params"] = kwargs
    return guard.run(
        provider="anthropic",
        operation="messages.create",
        request=request_payload,
        model=model,
        metadata=metadata,
        tenant_id=tenant_id,
        invoke=lambda: create(model=model, messages=messages, **kwargs),
    )
