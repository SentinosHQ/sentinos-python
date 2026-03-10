from __future__ import annotations

import asyncio
import contextlib
import importlib
from dataclasses import dataclass
from typing import Any

from ..models.decision_trace import DecisionTrace
from .llm import LLMGuard, LLMPolicyDeniedError, LLMPolicyEscalationError, LLMPolicyResult


class BedrockProviderError(RuntimeError):
    """Base provider-side error raised when Bedrock invocation fails after policy authorization."""

    def __init__(self, message: str, *, error_code: str | None = None, raw: Any | None = None):
        super().__init__(message)
        self.error_code = error_code
        self.raw = raw


class BedrockAccessDeniedError(BedrockProviderError):
    """Raised when Bedrock denies access to the target model or API."""


class BedrockThrottlingError(BedrockProviderError):
    """Raised when Bedrock throttles the request."""


class BedrockValidationError(BedrockProviderError):
    """Raised when Bedrock rejects request payload shape or unsupported fields."""


@dataclass(frozen=True)
class BedrockConverseStreamResult:
    provider: str
    operation: str
    decision: str
    trace: DecisionTrace
    events: list[dict[str, Any]]
    output_text: str
    stop_reason: str | None
    usage: dict[str, Any] | None
    metrics: dict[str, Any] | None


def _import_optional(module_name: str, extra_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ImportError(
            f"Optional dependency '{module_name}' is not installed. Install with: pip install 'sentinos[{extra_name}]'"
        ) from exc


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
        return getattr(value, "model_dump")()
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        return getattr(value, "to_dict")()
    if hasattr(value, "dict") and callable(getattr(value, "dict")):
        return getattr(value, "dict")()
    if hasattr(value, "__dict__"):
        return {str(k): v for k, v in vars(value).items() if not str(k).startswith("_")}
    raise TypeError(f"Unable to normalize payload from type {type(value).__name__}")


def _extract_error_code(exc: Exception) -> tuple[str | None, str]:
    message = str(exc)
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        err = response.get("Error")
        if isinstance(err, dict):
            code = err.get("Code")
            if isinstance(err.get("Message"), str) and err["Message"]:
                message = err["Message"]
            if isinstance(code, str) and code:
                return code, message
    code_attr = getattr(exc, "code", None)
    if isinstance(code_attr, str) and code_attr:
        return code_attr, message
    return None, message


def _raise_mapped_bedrock_error(exc: Exception) -> None:
    code, message = _extract_error_code(exc)
    prefix = f"Bedrock error {code}" if code else "Bedrock error"
    full = f"{prefix}: {message}"

    if code == "AccessDeniedException":
        raise BedrockAccessDeniedError(full, error_code=code, raw=exc) from exc
    if code == "ThrottlingException":
        raise BedrockThrottlingError(full, error_code=code, raw=exc) from exc
    if code == "ValidationException":
        raise BedrockValidationError(full, error_code=code, raw=exc) from exc
    raise BedrockProviderError(full, error_code=code, raw=exc) from exc


def _build_converse_payload(
    *,
    model_id: str,
    messages: list[dict[str, Any]],
    system: list[dict[str, Any]] | None = None,
    inference_config: dict[str, Any] | None = None,
    tool_config: dict[str, Any] | None = None,
    guardrail_config: dict[str, Any] | None = None,
    additional_model_request_fields: dict[str, Any] | None = None,
    additional_model_response_field_paths: list[str] | None = None,
    request_metadata: dict[str, str] | None = None,
    performance_config: dict[str, Any] | None = None,
    prompt_variables: dict[str, Any] | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "modelId": model_id,
        "messages": messages,
    }
    if system is not None:
        payload["system"] = system
    if inference_config is not None:
        payload["inferenceConfig"] = inference_config
    if tool_config is not None:
        payload["toolConfig"] = tool_config
    if guardrail_config is not None:
        payload["guardrailConfig"] = guardrail_config
    if additional_model_request_fields is not None:
        payload["additionalModelRequestFields"] = additional_model_request_fields
    if additional_model_response_field_paths is not None:
        payload["additionalModelResponseFieldPaths"] = additional_model_response_field_paths
    if request_metadata is not None:
        payload["requestMetadata"] = request_metadata
    if performance_config is not None:
        payload["performanceConfig"] = performance_config
    if prompt_variables is not None:
        payload["promptVariables"] = prompt_variables
    if extra_fields:
        payload.update(extra_fields)
    return payload


def _summarize_converse_response(response: dict[str, Any]) -> dict[str, Any]:
    output_message = response.get("output", {}).get("message") if isinstance(response.get("output"), dict) else None
    output_text: list[str] = []
    if isinstance(output_message, dict):
        content = output_message.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        output_text.append(text)

    summary: dict[str, Any] = {
        "stopReason": response.get("stopReason"),
        "output_text": "".join(output_text),
    }
    usage = response.get("usage")
    if isinstance(usage, dict):
        summary["usage"] = usage
    metrics = response.get("metrics")
    if isinstance(metrics, dict):
        summary["metrics"] = metrics
    return summary


def _collect_stream(
    raw_response: Any,
) -> tuple[list[dict[str, Any]], str, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    response_dict = _to_payload(raw_response)
    raw_stream = response_dict.get("stream")
    if raw_stream is None:
        return [], "", None, None, None

    events: list[dict[str, Any]] = []
    output_parts: list[str] = []
    stop_reason: str | None = None
    usage: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None

    for raw_event in raw_stream:
        event = _to_payload(raw_event)
        events.append(event)

        content_delta = event.get("contentBlockDelta")
        if isinstance(content_delta, dict):
            delta = content_delta.get("delta")
            if isinstance(delta, dict):
                text = delta.get("text")
                if isinstance(text, str):
                    output_parts.append(text)

        message_stop = event.get("messageStop")
        if isinstance(message_stop, dict):
            reason = message_stop.get("stopReason")
            if isinstance(reason, str):
                stop_reason = reason

        metadata = event.get("metadata")
        if isinstance(metadata, dict):
            maybe_usage = metadata.get("usage")
            if isinstance(maybe_usage, dict):
                usage = maybe_usage
            maybe_metrics = metadata.get("metrics")
            if isinstance(maybe_metrics, dict):
                metrics = maybe_metrics

    output_text = "".join(output_parts)
    return events, output_text, stop_reason, usage, metrics


@dataclass
class BedrockConverseAdapter:
    guard: LLMGuard
    client: Any
    provider: str = "bedrock"

    def converse(
        self,
        *,
        model_id: str,
        messages: list[dict[str, Any]],
        system: list[dict[str, Any]] | None = None,
        inference_config: dict[str, Any] | None = None,
        tool_config: dict[str, Any] | None = None,
        guardrail_config: dict[str, Any] | None = None,
        additional_model_request_fields: dict[str, Any] | None = None,
        additional_model_response_field_paths: list[str] | None = None,
        request_metadata: dict[str, str] | None = None,
        performance_config: dict[str, Any] | None = None,
        prompt_variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[dict[str, Any]]:
        payload = _build_converse_payload(
            model_id=model_id,
            messages=messages,
            system=system,
            inference_config=inference_config,
            tool_config=tool_config,
            guardrail_config=guardrail_config,
            additional_model_request_fields=additional_model_request_fields,
            additional_model_response_field_paths=additional_model_response_field_paths,
            request_metadata=request_metadata,
            performance_config=performance_config,
            prompt_variables=prompt_variables,
            extra_fields=kwargs,
        )
        trace = self.guard.authorize(
            provider=self.provider,
            operation="converse",
            request=payload,
            model=model_id,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        _ensure_allowed(provider=self.provider, operation="converse", trace=trace)

        try:
            raw_response = self.client.converse(**payload)
        except Exception as exc:
            _raise_mapped_bedrock_error(exc)

        response = _to_payload(raw_response)
        with contextlib.suppress(Exception):
            self.guard.record_response(
                provider=self.provider,
                operation="converse",
                trace=trace,
                response=response,
                tenant_id=tenant_id,
                response_summarizer=_summarize_converse_response,
            )
        return LLMPolicyResult(provider=self.provider, operation="converse", trace=trace, response=response)

    def converse_stream(
        self,
        *,
        model_id: str,
        messages: list[dict[str, Any]],
        system: list[dict[str, Any]] | None = None,
        inference_config: dict[str, Any] | None = None,
        tool_config: dict[str, Any] | None = None,
        guardrail_config: dict[str, Any] | None = None,
        additional_model_request_fields: dict[str, Any] | None = None,
        additional_model_response_field_paths: list[str] | None = None,
        request_metadata: dict[str, str] | None = None,
        performance_config: dict[str, Any] | None = None,
        prompt_variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> BedrockConverseStreamResult:
        payload = _build_converse_payload(
            model_id=model_id,
            messages=messages,
            system=system,
            inference_config=inference_config,
            tool_config=tool_config,
            guardrail_config=guardrail_config,
            additional_model_request_fields=additional_model_request_fields,
            additional_model_response_field_paths=additional_model_response_field_paths,
            request_metadata=request_metadata,
            performance_config=performance_config,
            prompt_variables=prompt_variables,
            extra_fields=kwargs,
        )
        trace = self.guard.authorize(
            provider=self.provider,
            operation="converse_stream",
            request=payload,
            model=model_id,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        decision = _ensure_allowed(provider=self.provider, operation="converse_stream", trace=trace)

        try:
            raw_response = self.client.converse_stream(**payload)
            events, output_text, stop_reason, usage, metrics = _collect_stream(raw_response)
        except Exception as exc:
            _raise_mapped_bedrock_error(exc)

        with contextlib.suppress(Exception):
            self.guard.record_response(
                provider=self.provider,
                operation="converse_stream",
                trace=trace,
                response={
                    "output_text": output_text,
                    "stopReason": stop_reason,
                    "usage": usage,
                    "metrics": metrics,
                    "events": len(events),
                },
                tenant_id=tenant_id,
            )
        return BedrockConverseStreamResult(
            provider=self.provider,
            operation="converse_stream",
            decision=decision,
            trace=trace,
            events=events,
            output_text=output_text,
            stop_reason=stop_reason,
            usage=usage,
            metrics=metrics,
        )


@dataclass
class AsyncBedrockConverseAdapter:
    guard: LLMGuard
    client: Any
    provider: str = "bedrock"

    async def converse(
        self,
        *,
        model_id: str,
        messages: list[dict[str, Any]],
        system: list[dict[str, Any]] | None = None,
        inference_config: dict[str, Any] | None = None,
        tool_config: dict[str, Any] | None = None,
        guardrail_config: dict[str, Any] | None = None,
        additional_model_request_fields: dict[str, Any] | None = None,
        additional_model_response_field_paths: list[str] | None = None,
        request_metadata: dict[str, str] | None = None,
        performance_config: dict[str, Any] | None = None,
        prompt_variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> LLMPolicyResult[dict[str, Any]]:
        payload = _build_converse_payload(
            model_id=model_id,
            messages=messages,
            system=system,
            inference_config=inference_config,
            tool_config=tool_config,
            guardrail_config=guardrail_config,
            additional_model_request_fields=additional_model_request_fields,
            additional_model_response_field_paths=additional_model_response_field_paths,
            request_metadata=request_metadata,
            performance_config=performance_config,
            prompt_variables=prompt_variables,
            extra_fields=kwargs,
        )
        trace = await self.guard.authorize_async(
            provider=self.provider,
            operation="converse",
            request=payload,
            model=model_id,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        _ensure_allowed(provider=self.provider, operation="converse", trace=trace)

        try:
            raw_response = await asyncio.to_thread(self.client.converse, **payload)
        except Exception as exc:
            _raise_mapped_bedrock_error(exc)

        response = _to_payload(raw_response)
        with contextlib.suppress(Exception):
            await self.guard.record_response_async(
                provider=self.provider,
                operation="converse",
                trace=trace,
                response=response,
                tenant_id=tenant_id,
                response_summarizer=_summarize_converse_response,
            )
        return LLMPolicyResult(provider=self.provider, operation="converse", trace=trace, response=response)

    async def converse_stream(
        self,
        *,
        model_id: str,
        messages: list[dict[str, Any]],
        system: list[dict[str, Any]] | None = None,
        inference_config: dict[str, Any] | None = None,
        tool_config: dict[str, Any] | None = None,
        guardrail_config: dict[str, Any] | None = None,
        additional_model_request_fields: dict[str, Any] | None = None,
        additional_model_response_field_paths: list[str] | None = None,
        request_metadata: dict[str, str] | None = None,
        performance_config: dict[str, Any] | None = None,
        prompt_variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        **kwargs: Any,
    ) -> BedrockConverseStreamResult:
        payload = _build_converse_payload(
            model_id=model_id,
            messages=messages,
            system=system,
            inference_config=inference_config,
            tool_config=tool_config,
            guardrail_config=guardrail_config,
            additional_model_request_fields=additional_model_request_fields,
            additional_model_response_field_paths=additional_model_response_field_paths,
            request_metadata=request_metadata,
            performance_config=performance_config,
            prompt_variables=prompt_variables,
            extra_fields=kwargs,
        )
        trace = await self.guard.authorize_async(
            provider=self.provider,
            operation="converse_stream",
            request=payload,
            model=model_id,
            metadata=metadata,
            tenant_id=tenant_id,
        )
        decision = _ensure_allowed(provider=self.provider, operation="converse_stream", trace=trace)

        try:
            raw_response = await asyncio.to_thread(self.client.converse_stream, **payload)
            events, output_text, stop_reason, usage, metrics = await asyncio.to_thread(_collect_stream, raw_response)
        except Exception as exc:
            _raise_mapped_bedrock_error(exc)

        with contextlib.suppress(Exception):
            await self.guard.record_response_async(
                provider=self.provider,
                operation="converse_stream",
                trace=trace,
                response={
                    "output_text": output_text,
                    "stopReason": stop_reason,
                    "usage": usage,
                    "metrics": metrics,
                    "events": len(events),
                },
                tenant_id=tenant_id,
            )
        return BedrockConverseStreamResult(
            provider=self.provider,
            operation="converse_stream",
            decision=decision,
            trace=trace,
            events=events,
            output_text=output_text,
            stop_reason=stop_reason,
            usage=usage,
            metrics=metrics,
        )


def _create_bedrock_runtime_client(
    *,
    client: Any | None = None,
    session: Any | None = None,
    region_name: str | None = None,
    profile_name: str | None = None,
    endpoint_url: str | None = None,
    **client_kwargs: Any,
) -> Any:
    if client is not None:
        return client

    boto3_module = _import_optional("boto3", "bedrock")

    resolved_session = session
    if resolved_session is None:
        session_kwargs: dict[str, Any] = {}
        if profile_name is not None:
            session_kwargs["profile_name"] = profile_name
        if region_name is not None:
            session_kwargs["region_name"] = region_name
        resolved_session = boto3_module.Session(**session_kwargs)

    kwargs: dict[str, Any] = dict(client_kwargs)
    if endpoint_url is not None:
        kwargs["endpoint_url"] = endpoint_url
    if region_name is not None and session is not None:
        kwargs["region_name"] = region_name

    return resolved_session.client("bedrock-runtime", **kwargs)


def create_bedrock_converse_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    session: Any | None = None,
    region_name: str | None = None,
    profile_name: str | None = None,
    endpoint_url: str | None = None,
    provider: str = "bedrock",
    **client_kwargs: Any,
) -> BedrockConverseAdapter:
    runtime_client = _create_bedrock_runtime_client(
        client=client,
        session=session,
        region_name=region_name,
        profile_name=profile_name,
        endpoint_url=endpoint_url,
        **client_kwargs,
    )
    return BedrockConverseAdapter(guard=guard, client=runtime_client, provider=provider)


def create_async_bedrock_converse_adapter(
    *,
    guard: LLMGuard,
    client: Any | None = None,
    session: Any | None = None,
    region_name: str | None = None,
    profile_name: str | None = None,
    endpoint_url: str | None = None,
    provider: str = "bedrock",
    **client_kwargs: Any,
) -> AsyncBedrockConverseAdapter:
    runtime_client = _create_bedrock_runtime_client(
        client=client,
        session=session,
        region_name=region_name,
        profile_name=profile_name,
        endpoint_url=endpoint_url,
        **client_kwargs,
    )
    return AsyncBedrockConverseAdapter(guard=guard, client=runtime_client, provider=provider)
