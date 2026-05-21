from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

from ..kernel import KernelClient
from ..models.decision_trace import DecisionTrace

T = TypeVar("T")

_FORBIDDEN_RATIONALE_KEYS = {
    "chain_of_thought",
    "hidden_reasoning",
    "raw_prompt",
    "raw_prompts",
    "prompt",
    "prompts",
    "messages",
    "raw_messages",
    "tool_args",
    "raw_tool_args",
    "tool_output",
    "raw_tool_output",
    "tool_outputs",
    "raw_tool_outputs",
}


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


def _sanitize_rationale(rationale: dict[str, Any] | None) -> tuple[dict[str, Any], list[str], bool]:
    if not rationale:
        return {}, [], False
    sanitized: dict[str, Any] = {}
    forbidden: list[str] = []
    hidden_reasoning_dropped = False
    for key, value in rationale.items():
        if key in _FORBIDDEN_RATIONALE_KEYS:
            forbidden.append(f"$.metadata.agent_rationale.{key}")
            if key in {"chain_of_thought", "hidden_reasoning"}:
                hidden_reasoning_dropped = True
            continue
        sanitized[key] = value
    return sanitized, forbidden, hidden_reasoning_dropped


def _metadata_rationale(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    candidate = metadata.get("agent_rationale") if metadata else None
    if isinstance(candidate, dict):
        return candidate
    return None


def _merge_rationale_inputs(
    metadata: dict[str, Any] | None,
    rationale: dict[str, Any] | None,
) -> dict[str, Any] | None:
    from_metadata = _metadata_rationale(metadata)
    if from_metadata is None:
        return rationale
    return {**from_metadata, **(rationale or {})}


def build_agent_rationale(
    *,
    provider: str,
    operation: str,
    model: str | None = None,
    tool: str | None = None,
    integration: str = "llm_guard",
    rationale: dict[str, Any] | None = None,
) -> dict[str, Any]:
    structured, forbidden, hidden_reasoning_dropped = _sanitize_rationale(rationale)
    has_structured = any(key not in {"workflow", "autonomy"} for key in structured)
    sources = [{"kind": "sdk", "field_paths": ["provider", "operation", "model", "tool_name"]}]
    if has_structured:
        sources.append({"kind": "workflow", "field_paths": ["metadata.agent_rationale"]})

    safety: dict[str, Any] = {}
    if hidden_reasoning_dropped:
        safety["hidden_reasoning_dropped"] = True
    if forbidden:
        safety["forbidden_fields"] = forbidden

    return {
        "schema_version": "agent-rationale.v1",
        "captured_at": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "capture_phase": "pre_execution",
        "capture_mode": "mixed" if has_structured else "sdk_derived",
        "sources": sources,
        "summary": structured.get("summary") or f"Authorize {provider}.{operation} before execution.",
        "goal": structured.get("goal"),
        "decision_basis": structured.get("decision_basis")
        or [
            f"Provider: {provider}",
            f"Operation: {operation}",
            *([f"Model: {model}"] if model else []),
            *([f"Tool: {tool}"] if tool else []),
        ],
        "expected_outcome": structured.get("expected_outcome"),
        "alternatives_considered": structured.get("alternatives_considered"),
        "confidence": structured.get("confidence"),
        "runtime": {
            "integration": integration,
            "provider": provider,
            "model": model,
            "operation": operation,
            "tool": tool,
            "workflow": structured.get("workflow"),
            "autonomy": structured.get("autonomy"),
        },
        "risk_context": structured.get("risk_context"),
        "safety": safety,
    }


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
        model: str | None = None,
        tool: str | None = None,
        rationale: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {
            "skip_connector": True,
            "integration_kind": "llm",
            "provider": provider,
            "operation": operation,
        }
        if metadata:
            merged.update(metadata)
        structured_rationale = _merge_rationale_inputs(metadata, rationale)
        merged["agent_rationale"] = build_agent_rationale(
            provider=provider,
            operation=operation,
            model=model,
            tool=tool,
            rationale=structured_rationale,
        )
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
        rationale: dict[str, Any] | None = None,
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
            metadata=self._merged_metadata(
                provider=provider,
                operation=operation,
                metadata=metadata,
                model=model,
                tool=tool,
                rationale=rationale,
            ),
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
        rationale: dict[str, Any] | None = None,
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
            metadata=self._merged_metadata(
                provider=provider,
                operation=operation,
                metadata=metadata,
                model=model,
                tool=tool,
                rationale=rationale,
            ),
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
        rationale: dict[str, Any] | None = None,
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
            rationale=rationale,
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
        rationale: dict[str, Any] | None = None,
    ) -> Iterator[DecisionTrace]:
        trace = self.authorize(
            provider=provider,
            operation=operation,
            request=request,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            tool_name=tool_name,
            rationale=rationale,
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
        rationale: dict[str, Any] | None = None,
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
            rationale=rationale,
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
        rationale: dict[str, Any] | None = None,
    ) -> AsyncIterator[DecisionTrace]:
        trace = await self.authorize_async(
            provider=provider,
            operation=operation,
            request=request,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            tool_name=tool_name,
            rationale=rationale,
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
    rationale: dict[str, Any] | None = None,
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
        rationale=rationale,
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
    rationale: dict[str, Any] | None = None,
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
        rationale=rationale,
        tenant_id=tenant_id,
        invoke=lambda: create(model=model, messages=messages, **kwargs),
    )
