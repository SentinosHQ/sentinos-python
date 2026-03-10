from __future__ import annotations

import contextlib
import importlib
import json
import os
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Iterable, Iterator
from dataclasses import dataclass
from itertools import chain
from typing import Any, TypeVar

from ..models.decision_trace import DecisionTrace
from ..models.openresponses import OpenResponsesRequest, OpenResponsesResponse, OpenResponsesStreamEvent
from .llm import LLMGuard, LLMPolicyDeniedError, LLMPolicyEscalationError, LLMPolicyResult

T = TypeVar("T")


def _import_optional(module_name: str, extra_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ImportError(
            f"Optional dependency '{module_name}' is not installed. Install with: pip install 'sentinos[{extra_name}]'"
        ) from exc


def _require_attr(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if not hasattr(cur, part):
            raise AttributeError(f"Expected attribute '{path}' was not found on {type(obj).__name__}")
        cur = getattr(cur, part)
    return cur


def _resolve_openrouter_api_key(api_key: str | None) -> str | None:
    if api_key is not None:
        return api_key
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key is None:
        return None
    value = env_key.strip()
    return value if value else None


def _openrouter_default_headers(
    *,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {}
    if http_referer is not None and http_referer.strip():
        headers["HTTP-Referer"] = http_referer.strip()
    if x_title is not None and x_title.strip():
        headers["X-Title"] = x_title.strip()
    return headers


def _decision_text(trace: DecisionTrace) -> str:
    return str(trace.decision).strip().upper()


def _ensure_allowed(*, provider: str, operation: str, trace: DecisionTrace) -> str:
    decision = _decision_text(trace)
    reason = trace.policy_evaluation.reason or "policy decision"
    if decision == "DENY":
        raise LLMPolicyDeniedError(f"Sentinos denied {provider}.{operation}: {reason}", trace=trace)
    if decision == "ESCALATE":
        raise LLMPolicyEscalationError(f"Sentinos escalated {provider}.{operation}: {reason}", trace=trace)
    return decision


def _to_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump") and callable(getattr(value, "model_dump")):
        model_dump = getattr(value, "model_dump")
        return model_dump()
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        to_dict = getattr(value, "to_dict")
        return to_dict()
    if hasattr(value, "dict") and callable(getattr(value, "dict")):
        dict_fn = getattr(value, "dict")
        return dict_fn()
    if hasattr(value, "__dict__"):
        raw = vars(value)
        return {str(k): v for k, v in raw.items() if not str(k).startswith("_")}
    raise TypeError(f"Unable to normalize payload from type {type(value).__name__}")


def _normalize_response(value: Any) -> OpenResponsesResponse:
    if isinstance(value, OpenResponsesResponse):
        return value
    return OpenResponsesResponse.model_validate(_to_payload(value))


def _summarize_response(response: OpenResponsesResponse) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "id": response.id,
        "status": response.status,
        "model": response.model,
        "output_items": len(response.output or []),
    }
    if response.usage is not None:
        summary["usage"] = response.usage.model_dump(exclude_none=True)
    return summary


def parse_openresponses_sse_event(
    raw: OpenResponsesStreamEvent | dict[str, Any] | str | bytes,
    *,
    event_name: str | None = None,
) -> OpenResponsesStreamEvent | None:
    if isinstance(raw, OpenResponsesStreamEvent):
        return raw

    payload: dict[str, Any]
    if isinstance(raw, dict):
        payload = raw
    else:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        line = text.strip()
        if not line:
            return None
        if line.startswith("data:"):
            line = line[5:].strip()
        if line == "[DONE]":
            return OpenResponsesStreamEvent(type="response.done")
        loaded = json.loads(line)
        if not isinstance(loaded, dict):
            raise ValueError("Open Responses SSE data payload must decode to an object")
        payload = loaded

    if event_name and "type" not in payload:
        payload = dict(payload)
        payload["type"] = event_name
    return OpenResponsesStreamEvent.model_validate(payload)


def iter_openresponses_sse_lines(lines: Iterable[str]) -> Iterator[OpenResponsesStreamEvent]:
    event_name: str | None = None
    data_lines: list[str] = []

    def flush() -> OpenResponsesStreamEvent | None:
        nonlocal event_name, data_lines
        if event_name is None and not data_lines:
            return None
        payload = "\n".join(data_lines).strip()
        out = parse_openresponses_sse_event(payload if payload else "{}", event_name=event_name)
        event_name = None
        data_lines = []
        return out

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line == "":
            event = flush()
            if event is not None:
                yield event
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_name = line[6:].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
            continue
        # Accept JSON-lines style streams where lines are full payloads.
        data_lines.append(line.strip())

    tail = flush()
    if tail is not None:
        yield tail


async def aiter_openresponses_sse_lines(lines: AsyncIterable[str]) -> AsyncIterator[OpenResponsesStreamEvent]:
    event_name: str | None = None
    data_lines: list[str] = []

    async def flush() -> OpenResponsesStreamEvent | None:
        nonlocal event_name, data_lines
        if event_name is None and not data_lines:
            return None
        payload = "\n".join(data_lines).strip()
        out = parse_openresponses_sse_event(payload if payload else "{}", event_name=event_name)
        event_name = None
        data_lines = []
        return out

    async for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line == "":
            event = await flush()
            if event is not None:
                yield event
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_name = line[6:].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
            continue
        data_lines.append(line.strip())

    tail = await flush()
    if tail is not None:
        yield tail


def _iter_items(stream_obj: Any) -> Iterator[Any]:
    if hasattr(stream_obj, "events") and callable(getattr(stream_obj, "events")):
        yield from stream_obj.events()
        return
    if hasattr(stream_obj, "iter_lines") and callable(getattr(stream_obj, "iter_lines")):
        yield from stream_obj.iter_lines()
        return
    if isinstance(stream_obj, Iterable) and not isinstance(stream_obj, (str, bytes, dict)):
        yield from stream_obj
        return
    raise TypeError(f"Unsupported stream object type: {type(stream_obj).__name__}")


async def _aiter_items(stream_obj: Any) -> AsyncIterator[Any]:
    if hasattr(stream_obj, "__aiter__"):
        async for item in stream_obj:
            yield item
        return
    if hasattr(stream_obj, "aiter_lines") and callable(getattr(stream_obj, "aiter_lines")):
        async for line in stream_obj.aiter_lines():
            yield line
        return
    if isinstance(stream_obj, Iterable) and not isinstance(stream_obj, (str, bytes, dict)):
        for item in stream_obj:
            yield item
        return
    raise TypeError(f"Unsupported async stream object type: {type(stream_obj).__name__}")


def _extract_final_response(stream_obj: Any) -> OpenResponsesResponse | None:
    getter = getattr(stream_obj, "get_final_response", None)
    if getter is None or not callable(getter):
        return None
    with contextlib.suppress(Exception):
        return _normalize_response(getter())
    return None


@dataclass(frozen=True)
class OpenResponsesStreamResult:
    provider: str
    operation: str
    decision: str
    trace: DecisionTrace
    events: list[OpenResponsesStreamEvent]
    final_response: OpenResponsesResponse | None = None


@dataclass
class OpenResponsesAdapter:
    """
    Governance adapter for Open Responses-style `responses.create` integrations.

    Supports:
    - OpenAI Responses compatible clients
    - provider/router endpoints implementing the Open Responses schema
    - custom callables via `create_fn` / `stream_fn`
    """

    guard: LLMGuard
    create_fn: Callable[..., Any]
    stream_fn: Callable[..., Any] | None = None
    provider: str = "openresponses"
    operation: str = "responses.create"
    create_uses_body: bool = False
    stream_uses_body: bool = False

    @classmethod
    def from_client(cls, *, guard: LLMGuard, client: Any) -> OpenResponsesAdapter:
        create_fn = _require_attr(client, "responses.create")
        stream_fn = None
        with contextlib.suppress(AttributeError):
            candidate = _require_attr(client, "responses.stream")
            if callable(candidate):
                stream_fn = candidate
        return cls(guard=guard, create_fn=create_fn, stream_fn=stream_fn)

    def _build_body(self, *, model: str, input: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        request = OpenResponsesRequest.model_validate({"model": model, "input": input, **kwargs})
        return request.model_dump(exclude_none=True)

    def _invoke_create(self, body: dict[str, Any]) -> OpenResponsesResponse:
        raw = self.create_fn(body) if self.create_uses_body else self.create_fn(**body)
        return _normalize_response(raw)

    def create(
        self,
        *,
        model: str,
        input: Any,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[OpenResponsesResponse]:
        body = self._build_body(model=model, input=input, kwargs=kwargs)
        return self.guard.run(
            provider=self.provider,
            operation=self.operation,
            request=body,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self._invoke_create(body),
            response_summarizer=_summarize_response,
        )

    def create_request(
        self,
        *,
        request: OpenResponsesRequest | dict[str, Any],
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> LLMPolicyResult[OpenResponsesResponse]:
        body = request.model_dump(exclude_none=True) if isinstance(request, OpenResponsesRequest) else dict(request)
        model_raw = body.get("model")
        model = model_raw if isinstance(model_raw, str) else None
        return self.guard.run(
            provider=self.provider,
            operation=self.operation,
            request=body,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self._invoke_create(body),
            response_summarizer=_summarize_response,
        )

    def _collect_stream(self, stream_obj: Any) -> tuple[list[OpenResponsesStreamEvent], OpenResponsesResponse | None]:
        events: list[OpenResponsesStreamEvent] = []
        final_response: OpenResponsesResponse | None = None

        iterator = _iter_items(stream_obj)
        try:
            first = next(iterator)
        except StopIteration:
            return events, _extract_final_response(stream_obj)

        joined = chain([first], iterator)
        if isinstance(first, (str, bytes)):
            normalized_lines = (
                line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line for line in joined
            )
            for event in iter_openresponses_sse_lines(normalized_lines):
                events.append(event)
                if event.response is not None:
                    final_response = event.response
        else:
            for raw in joined:
                event = OpenResponsesStreamEvent.model_validate(_to_payload(raw))
                events.append(event)
                if event.response is not None:
                    final_response = event.response

        if final_response is None:
            final_response = _extract_final_response(stream_obj)
        return events, final_response

    def stream(
        self,
        *,
        model: str,
        input: Any,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> OpenResponsesStreamResult:
        if self.stream_fn is None:
            raise ValueError("stream_fn is not configured; provide one or use a client exposing responses.stream")

        body = self._build_body(model=model, input=input, kwargs={**kwargs, "stream": True})
        trace = self.guard.authorize(
            provider=self.provider,
            operation=self.operation,
            request=body,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        decision = _ensure_allowed(provider=self.provider, operation=self.operation, trace=trace)

        raw_stream = self.stream_fn(body) if self.stream_uses_body else self.stream_fn(**body)
        if hasattr(raw_stream, "__enter__") and hasattr(raw_stream, "__exit__"):
            with raw_stream as active_stream:
                events, final_response = self._collect_stream(active_stream)
        else:
            events, final_response = self._collect_stream(raw_stream)

        if final_response is not None:
            with contextlib.suppress(Exception):
                self.guard.record_response(
                    provider=self.provider,
                    operation=self.operation,
                    trace=trace,
                    response=final_response,
                    tenant_id=tenant_id,
                    response_summarizer=lambda r: _summarize_response(_normalize_response(r)),
                )
        return OpenResponsesStreamResult(
            provider=self.provider,
            operation=self.operation,
            decision=decision,
            trace=trace,
            events=events,
            final_response=final_response,
        )


@dataclass
class AsyncOpenResponsesAdapter:
    guard: LLMGuard
    create_fn: Callable[..., Awaitable[Any]]
    stream_fn: Callable[..., Awaitable[Any] | Any] | None = None
    provider: str = "openresponses"
    operation: str = "responses.create"
    create_uses_body: bool = False
    stream_uses_body: bool = False

    @classmethod
    def from_client(cls, *, guard: LLMGuard, client: Any) -> AsyncOpenResponsesAdapter:
        create_fn = _require_attr(client, "responses.create")
        stream_fn = None
        with contextlib.suppress(AttributeError):
            candidate = _require_attr(client, "responses.stream")
            if callable(candidate):
                stream_fn = candidate
        return cls(guard=guard, create_fn=create_fn, stream_fn=stream_fn)

    def _build_body(self, *, model: str, input: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        request = OpenResponsesRequest.model_validate({"model": model, "input": input, **kwargs})
        return request.model_dump(exclude_none=True)

    async def _invoke_create(self, body: dict[str, Any]) -> OpenResponsesResponse:
        raw = await (self.create_fn(body) if self.create_uses_body else self.create_fn(**body))
        return _normalize_response(raw)

    async def create(
        self,
        *,
        model: str,
        input: Any,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[OpenResponsesResponse]:
        body = self._build_body(model=model, input=input, kwargs=kwargs)
        return await self.guard.run_async(
            provider=self.provider,
            operation=self.operation,
            request=body,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self._invoke_create(body),
            response_summarizer=_summarize_response,
        )

    async def create_request(
        self,
        *,
        request: OpenResponsesRequest | dict[str, Any],
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> LLMPolicyResult[OpenResponsesResponse]:
        body = request.model_dump(exclude_none=True) if isinstance(request, OpenResponsesRequest) else dict(request)
        model_raw = body.get("model")
        model = model_raw if isinstance(model_raw, str) else None
        return await self.guard.run_async(
            provider=self.provider,
            operation=self.operation,
            request=body,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self._invoke_create(body),
            response_summarizer=_summarize_response,
        )

    async def _collect_stream(
        self,
        stream_obj: Any,
    ) -> tuple[list[OpenResponsesStreamEvent], OpenResponsesResponse | None]:
        events: list[OpenResponsesStreamEvent] = []
        final_response: OpenResponsesResponse | None = None

        iterator = _aiter_items(stream_obj)
        try:
            first = await iterator.__anext__()
        except StopAsyncIteration:
            return events, _extract_final_response(stream_obj)

        if isinstance(first, (str, bytes)):

            async def line_iter() -> AsyncIterator[str]:
                first_line = first.decode("utf-8", errors="replace") if isinstance(first, bytes) else first
                yield first_line
                async for line in iterator:
                    yield line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line

            async for event in aiter_openresponses_sse_lines(line_iter()):
                events.append(event)
                if event.response is not None:
                    final_response = event.response
        else:
            first_event = OpenResponsesStreamEvent.model_validate(_to_payload(first))
            events.append(first_event)
            if first_event.response is not None:
                final_response = first_event.response
            async for raw in iterator:
                event = OpenResponsesStreamEvent.model_validate(_to_payload(raw))
                events.append(event)
                if event.response is not None:
                    final_response = event.response

        if final_response is None:
            final_response = _extract_final_response(stream_obj)
        return events, final_response

    async def stream(
        self,
        *,
        model: str,
        input: Any,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> OpenResponsesStreamResult:
        if self.stream_fn is None:
            raise ValueError("stream_fn is not configured; provide one or use a client exposing responses.stream")

        body = self._build_body(model=model, input=input, kwargs={**kwargs, "stream": True})
        trace = await self.guard.authorize_async(
            provider=self.provider,
            operation=self.operation,
            request=body,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        decision = _ensure_allowed(provider=self.provider, operation=self.operation, trace=trace)

        candidate = self.stream_fn(body) if self.stream_uses_body else self.stream_fn(**body)
        raw_stream = await candidate if isinstance(candidate, Awaitable) else candidate

        if hasattr(raw_stream, "__aenter__") and hasattr(raw_stream, "__aexit__"):
            async with raw_stream as active_stream:
                events, final_response = await self._collect_stream(active_stream)
        else:
            events, final_response = await self._collect_stream(raw_stream)

        if final_response is not None:
            with contextlib.suppress(Exception):
                await self.guard.record_response_async(
                    provider=self.provider,
                    operation=self.operation,
                    trace=trace,
                    response=final_response,
                    tenant_id=tenant_id,
                    response_summarizer=lambda r: _summarize_response(_normalize_response(r)),
                )
        return OpenResponsesStreamResult(
            provider=self.provider,
            operation=self.operation,
            decision=decision,
            trace=trace,
            events=events,
            final_response=final_response,
        )


def create_openresponses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    create_fn: Callable[..., Any] | None = None,
    stream_fn: Callable[..., Any] | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    organization: str | None = None,
    default_headers: dict[str, str] | None = None,
    provider: str = "openresponses",
    operation: str = "responses.create",
) -> OpenResponsesAdapter:
    if create_fn is not None:
        return OpenResponsesAdapter(
            guard=guard,
            create_fn=create_fn,
            stream_fn=stream_fn,
            provider=provider,
            operation=operation,
        )

    c = client
    if c is None:
        openai_module = _import_optional("openai", "openai")
        ctor = _require_attr(openai_module, "OpenAI")
        kwargs: dict[str, Any] = {}
        if api_key is not None:
            kwargs["api_key"] = api_key
        if base_url is not None:
            kwargs["base_url"] = base_url
        if organization is not None:
            kwargs["organization"] = organization
        if default_headers:
            kwargs["default_headers"] = default_headers
        c = ctor(**kwargs)
    adapter = OpenResponsesAdapter.from_client(guard=guard, client=c)
    adapter.provider = provider
    adapter.operation = operation
    if stream_fn is not None:
        adapter.stream_fn = stream_fn
    return adapter


def create_async_openresponses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    create_fn: Callable[..., Awaitable[Any]] | None = None,
    stream_fn: Callable[..., Awaitable[Any] | Any] | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    organization: str | None = None,
    default_headers: dict[str, str] | None = None,
    provider: str = "openresponses",
    operation: str = "responses.create",
) -> AsyncOpenResponsesAdapter:
    if create_fn is not None:
        return AsyncOpenResponsesAdapter(
            guard=guard,
            create_fn=create_fn,
            stream_fn=stream_fn,
            provider=provider,
            operation=operation,
        )

    c = client
    if c is None:
        openai_module = _import_optional("openai", "openai")
        ctor = _require_attr(openai_module, "AsyncOpenAI")
        kwargs: dict[str, Any] = {}
        if api_key is not None:
            kwargs["api_key"] = api_key
        if base_url is not None:
            kwargs["base_url"] = base_url
        if organization is not None:
            kwargs["organization"] = organization
        if default_headers:
            kwargs["default_headers"] = default_headers
        c = ctor(**kwargs)
    adapter = AsyncOpenResponsesAdapter.from_client(guard=guard, client=c)
    adapter.provider = provider
    adapter.operation = operation
    if stream_fn is not None:
        adapter.stream_fn = stream_fn
    return adapter


def create_openrouter_openresponses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    create_fn: Callable[..., Any] | None = None,
    stream_fn: Callable[..., Any] | None = None,
    api_key: str | None = None,
    base_url: str = "https://openrouter.ai/api/v1",
    organization: str | None = None,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> OpenResponsesAdapter:
    resolved_api_key = _resolve_openrouter_api_key(api_key)
    return create_openresponses_adapter(
        guard=guard,
        client=client,
        create_fn=create_fn,
        stream_fn=stream_fn,
        api_key=resolved_api_key,
        base_url=base_url,
        organization=organization,
        default_headers=_openrouter_default_headers(http_referer=http_referer, x_title=x_title),
        provider="openrouter",
        operation="responses.create",
    )


def create_async_openrouter_openresponses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    create_fn: Callable[..., Awaitable[Any]] | None = None,
    stream_fn: Callable[..., Awaitable[Any] | Any] | None = None,
    api_key: str | None = None,
    base_url: str = "https://openrouter.ai/api/v1",
    organization: str | None = None,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> AsyncOpenResponsesAdapter:
    resolved_api_key = _resolve_openrouter_api_key(api_key)
    return create_async_openresponses_adapter(
        guard=guard,
        client=client,
        create_fn=create_fn,
        stream_fn=stream_fn,
        api_key=resolved_api_key,
        base_url=base_url,
        organization=organization,
        default_headers=_openrouter_default_headers(http_referer=http_referer, x_title=x_title),
        provider="openrouter",
        operation="responses.create",
    )


def guard_openresponses_create(
    *,
    guard: LLMGuard,
    create: Callable[..., Any],
    model: str,
    input: Any,
    metadata: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    **kwargs: Any,
) -> LLMPolicyResult[OpenResponsesResponse]:
    adapter = OpenResponsesAdapter(guard=guard, create_fn=create)
    return adapter.create(model=model, input=input, metadata=metadata, tenant_id=tenant_id, **kwargs)
