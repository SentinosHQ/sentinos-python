from __future__ import annotations

import importlib
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from .llm import LLMGuard, LLMPolicyResult, guard_anthropic_messages

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


@dataclass
class OpenAIChatCompletionsAdapter(Generic[T]):
    """
    Thin adapter for OpenAI-style `chat.completions.create(...)` call signatures.

    Pass either:
    - a callable `create(...)`, or
    - an OpenAI-like client object exposing `.chat.completions.create`.
    """

    guard: LLMGuard
    create_fn: Callable[..., T]
    provider: str = "openai"

    @classmethod
    def from_client(
        cls,
        *,
        guard: LLMGuard,
        client: Any,
        provider: str = "openai",
    ) -> OpenAIChatCompletionsAdapter[Any]:
        create_fn = client.chat.completions.create
        return cls(guard=guard, create_fn=create_fn, provider=provider)

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[T]:
        request_payload: dict[str, Any] = {"model": model, "messages": messages}
        if kwargs:
            request_payload["params"] = kwargs
        return self.guard.run(
            provider=self.provider,
            operation="chat.completions",
            request=request_payload,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self.create_fn(model=model, messages=messages, **kwargs),
        )


@dataclass
class AsyncOpenAIChatCompletionsAdapter(Generic[T]):
    """
    Async adapter for OpenAI-style `chat.completions.create(...)` async call signatures.
    """

    guard: LLMGuard
    create_fn: Callable[..., Awaitable[T]]
    provider: str = "openai"

    @classmethod
    def from_client(
        cls,
        *,
        guard: LLMGuard,
        client: Any,
        provider: str = "openai",
    ) -> AsyncOpenAIChatCompletionsAdapter[Any]:
        create_fn = client.chat.completions.create
        return cls(guard=guard, create_fn=create_fn, provider=provider)

    async def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[T]:
        request_payload: dict[str, Any] = {"model": model, "messages": messages}
        if kwargs:
            request_payload["params"] = kwargs
        return await self.guard.run_async(
            provider=self.provider,
            operation="chat.completions",
            request=request_payload,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self.create_fn(model=model, messages=messages, **kwargs),
        )


@dataclass
class OpenAIResponsesAdapter(Generic[T]):
    """
    Adapter for OpenAI-style `responses.create(...)` call signatures.
    """

    guard: LLMGuard
    create_fn: Callable[..., T]
    provider: str = "openai"

    @classmethod
    def from_client(
        cls,
        *,
        guard: LLMGuard,
        client: Any,
        provider: str = "openai",
    ) -> OpenAIResponsesAdapter[Any]:
        create_fn = _require_attr(client, "responses.create")
        return cls(guard=guard, create_fn=create_fn, provider=provider)

    def create(
        self,
        *,
        model: str,
        input: Any,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[T]:
        request_payload: dict[str, Any] = {"model": model, "input": input}
        if kwargs:
            request_payload["params"] = kwargs
        return self.guard.run(
            provider=self.provider,
            operation="responses.create",
            request=request_payload,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self.create_fn(model=model, input=input, **kwargs),
        )


@dataclass
class AsyncOpenAIResponsesAdapter(Generic[T]):
    """
    Async adapter for OpenAI-style `responses.create(...)` call signatures.
    """

    guard: LLMGuard
    create_fn: Callable[..., Awaitable[T]]
    provider: str = "openai"

    @classmethod
    def from_client(
        cls,
        *,
        guard: LLMGuard,
        client: Any,
        provider: str = "openai",
    ) -> AsyncOpenAIResponsesAdapter[Any]:
        create_fn = _require_attr(client, "responses.create")
        return cls(guard=guard, create_fn=create_fn, provider=provider)

    async def create(
        self,
        *,
        model: str,
        input: Any,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[T]:
        request_payload: dict[str, Any] = {"model": model, "input": input}
        if kwargs:
            request_payload["params"] = kwargs
        return await self.guard.run_async(
            provider=self.provider,
            operation="responses.create",
            request=request_payload,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self.create_fn(model=model, input=input, **kwargs),
        )


@dataclass
class AnthropicMessagesAdapter(Generic[T]):
    """
    Thin adapter for Anthropic-style `messages.create(...)` call signatures.
    """

    guard: LLMGuard
    create_fn: Callable[..., T]

    @classmethod
    def from_client(cls, *, guard: LLMGuard, client: Any) -> AnthropicMessagesAdapter[Any]:
        create_fn = client.messages.create
        return cls(guard=guard, create_fn=create_fn)

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[T]:
        return guard_anthropic_messages(
            guard=self.guard,
            create=self.create_fn,
            model=model,
            messages=messages,
            metadata=metadata,
            tenant_id=tenant_id,
            **kwargs,
        )


@dataclass
class AsyncAnthropicMessagesAdapter(Generic[T]):
    """
    Async adapter for Anthropic-style `messages.create(...)` call signatures.
    """

    guard: LLMGuard
    create_fn: Callable[..., Awaitable[T]]

    @classmethod
    def from_client(cls, *, guard: LLMGuard, client: Any) -> AsyncAnthropicMessagesAdapter[Any]:
        create_fn = client.messages.create
        return cls(guard=guard, create_fn=create_fn)

    async def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[T]:
        request_payload: dict[str, Any] = {"model": model, "messages": messages}
        if kwargs:
            request_payload["params"] = kwargs
        return await self.guard.run_async(
            provider="anthropic",
            operation="messages.create",
            request=request_payload,
            model=model,
            metadata=metadata,
            tenant_id=tenant_id,
            invoke=lambda: self.create_fn(model=model, messages=messages, **kwargs),
        )


def create_openai_chat_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    organization: str | None = None,
) -> OpenAIChatCompletionsAdapter[Any]:
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
        c = ctor(**kwargs)
    return OpenAIChatCompletionsAdapter.from_client(guard=guard, client=c, provider="openai")


def create_async_openai_chat_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    organization: str | None = None,
) -> AsyncOpenAIChatCompletionsAdapter[Any]:
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
        c = ctor(**kwargs)
    return AsyncOpenAIChatCompletionsAdapter.from_client(guard=guard, client=c, provider="openai")


def create_openai_responses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    organization: str | None = None,
) -> OpenAIResponsesAdapter[Any]:
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
        c = ctor(**kwargs)
    return OpenAIResponsesAdapter.from_client(guard=guard, client=c, provider="openai")


def create_async_openai_responses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    organization: str | None = None,
) -> AsyncOpenAIResponsesAdapter[Any]:
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
        c = ctor(**kwargs)
    return AsyncOpenAIResponsesAdapter.from_client(guard=guard, client=c, provider="openai")


def create_openrouter_chat_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str = "https://openrouter.ai/api/v1",
    organization: str | None = None,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> OpenAIChatCompletionsAdapter[Any]:
    c = client
    if c is None:
        openai_module = _import_optional("openai", "openai")
        ctor = _require_attr(openai_module, "OpenAI")
        kwargs: dict[str, Any] = {
            "base_url": base_url,
        }
        resolved_api_key = _resolve_openrouter_api_key(api_key)
        if resolved_api_key is not None:
            kwargs["api_key"] = resolved_api_key
        if organization is not None:
            kwargs["organization"] = organization
        default_headers = _openrouter_default_headers(http_referer=http_referer, x_title=x_title)
        if default_headers:
            kwargs["default_headers"] = default_headers
        c = ctor(**kwargs)
    return OpenAIChatCompletionsAdapter.from_client(guard=guard, client=c, provider="openrouter")


def create_async_openrouter_chat_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str = "https://openrouter.ai/api/v1",
    organization: str | None = None,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> AsyncOpenAIChatCompletionsAdapter[Any]:
    c = client
    if c is None:
        openai_module = _import_optional("openai", "openai")
        ctor = _require_attr(openai_module, "AsyncOpenAI")
        kwargs: dict[str, Any] = {
            "base_url": base_url,
        }
        resolved_api_key = _resolve_openrouter_api_key(api_key)
        if resolved_api_key is not None:
            kwargs["api_key"] = resolved_api_key
        if organization is not None:
            kwargs["organization"] = organization
        default_headers = _openrouter_default_headers(http_referer=http_referer, x_title=x_title)
        if default_headers:
            kwargs["default_headers"] = default_headers
        c = ctor(**kwargs)
    return AsyncOpenAIChatCompletionsAdapter.from_client(guard=guard, client=c, provider="openrouter")


def create_openrouter_responses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str = "https://openrouter.ai/api/v1",
    organization: str | None = None,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> OpenAIResponsesAdapter[Any]:
    c = client
    if c is None:
        openai_module = _import_optional("openai", "openai")
        ctor = _require_attr(openai_module, "OpenAI")
        kwargs: dict[str, Any] = {
            "base_url": base_url,
        }
        resolved_api_key = _resolve_openrouter_api_key(api_key)
        if resolved_api_key is not None:
            kwargs["api_key"] = resolved_api_key
        if organization is not None:
            kwargs["organization"] = organization
        default_headers = _openrouter_default_headers(http_referer=http_referer, x_title=x_title)
        if default_headers:
            kwargs["default_headers"] = default_headers
        c = ctor(**kwargs)
    return OpenAIResponsesAdapter.from_client(guard=guard, client=c, provider="openrouter")


def create_async_openrouter_responses_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str = "https://openrouter.ai/api/v1",
    organization: str | None = None,
    http_referer: str | None = None,
    x_title: str | None = None,
) -> AsyncOpenAIResponsesAdapter[Any]:
    c = client
    if c is None:
        openai_module = _import_optional("openai", "openai")
        ctor = _require_attr(openai_module, "AsyncOpenAI")
        kwargs: dict[str, Any] = {
            "base_url": base_url,
        }
        resolved_api_key = _resolve_openrouter_api_key(api_key)
        if resolved_api_key is not None:
            kwargs["api_key"] = resolved_api_key
        if organization is not None:
            kwargs["organization"] = organization
        default_headers = _openrouter_default_headers(http_referer=http_referer, x_title=x_title)
        if default_headers:
            kwargs["default_headers"] = default_headers
        c = ctor(**kwargs)
    return AsyncOpenAIResponsesAdapter.from_client(guard=guard, client=c, provider="openrouter")


def create_anthropic_messages_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AnthropicMessagesAdapter[Any]:
    c = client
    if c is None:
        anthropic_module = _import_optional("anthropic", "anthropic")
        ctor = _require_attr(anthropic_module, "Anthropic")
        kwargs: dict[str, Any] = {}
        if api_key is not None:
            kwargs["api_key"] = api_key
        if base_url is not None:
            kwargs["base_url"] = base_url
        c = ctor(**kwargs)
    return AnthropicMessagesAdapter.from_client(guard=guard, client=c)


def create_async_anthropic_messages_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncAnthropicMessagesAdapter[Any]:
    c = client
    if c is None:
        anthropic_module = _import_optional("anthropic", "anthropic")
        ctor = _require_attr(anthropic_module, "AsyncAnthropic")
        kwargs: dict[str, Any] = {}
        if api_key is not None:
            kwargs["api_key"] = api_key
        if base_url is not None:
            kwargs["base_url"] = base_url
        c = ctor(**kwargs)
    return AsyncAnthropicMessagesAdapter.from_client(guard=guard, client=c)


def make_guarded_tool(
    *,
    guard: LLMGuard,
    tool_name: str,
    execute: Callable[..., T],
    provider: str = "tool-runtime",
) -> Callable[..., dict[str, Any]]:
    """
    Wrap a tool callback so Sentinos policy is evaluated before execution.

    Returned callable executes as:
    1) authorize tool invocation
    2) run tool only on ALLOW/SHADOW
    3) record response summary
    """

    def wrapped(**tool_args: Any) -> dict[str, Any]:
        trace = guard.authorize(
            provider=provider,
            operation=tool_name,
            request={"tool": tool_name, "args": tool_args},
            tool_name=f"tool.{tool_name}",
        )
        decision = str(trace.decision).upper()
        if decision not in {"ALLOW", "SHADOW"}:
            return {
                "trace_id": trace.trace_id,
                "decision": decision,
                "reason": trace.policy_evaluation.reason,
            }

        result = execute(**tool_args)
        try:
            guard.record_response(provider=provider, operation=tool_name, trace=trace, response=result)
        except Exception:
            pass
        return {"trace_id": trace.trace_id, "decision": decision, "result": result}

    return wrapped


def make_guarded_tool_async(
    *,
    guard: LLMGuard,
    tool_name: str,
    execute: Callable[..., Awaitable[T]],
    provider: str = "tool-runtime",
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """
    Async variant of make_guarded_tool.
    """

    async def wrapped(**tool_args: Any) -> dict[str, Any]:
        trace = await guard.authorize_async(
            provider=provider,
            operation=tool_name,
            request={"tool": tool_name, "args": tool_args},
            tool_name=f"tool.{tool_name}",
        )
        decision = str(trace.decision).upper()
        if decision not in {"ALLOW", "SHADOW"}:
            return {
                "trace_id": trace.trace_id,
                "decision": decision,
                "reason": trace.policy_evaluation.reason,
            }

        result = await execute(**tool_args)
        try:
            await guard.record_response_async(provider=provider, operation=tool_name, trace=trace, response=result)
        except Exception:
            pass
        return {"trace_id": trace.trace_id, "decision": decision, "result": result}

    return wrapped
