from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class OpenResponsesRequest(BaseModel):
    """
    Typed request envelope for the Open Responses-style `/responses` API.

    The schema is intentionally permissive (`extra="allow"`) so providers can
    add implementation-specific fields without breaking SDK callers.
    """

    model_config = ConfigDict(extra="allow")

    model: str
    input: Any

    previous_response_id: str | None = None
    include: list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    text: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None

    temperature: float | None = None
    top_p: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    max_output_tokens: int | None = None
    max_tool_calls: int | None = None
    top_logprobs: int | None = None

    parallel_tool_calls: bool | None = None
    stream: bool | None = None
    stream_options: dict[str, Any] | None = None

    background: bool | None = None
    truncation: str | None = None
    instructions: str | None = None
    store: bool | None = None
    service_tier: str | None = None
    safety_identifier: str | None = None
    prompt_cache_key: str | None = None


class OpenResponsesError(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: str | None = None
    type: str | None = None
    code: str | None = None
    param: str | None = None


class OpenResponsesUsage(BaseModel):
    model_config = ConfigDict(extra="allow")

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    input_tokens_details: dict[str, Any] | None = None
    output_tokens_details: dict[str, Any] | None = None


class OpenResponsesItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    id: str | None = None
    status: str | None = None

    role: str | None = None
    name: str | None = None
    call_id: str | None = None

    content: Any = None
    arguments: str | dict[str, Any] | None = None
    output: Any = None


class OpenResponsesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    object: str | None = None
    created_at: int | None = None
    completed_at: int | None = None
    status: str | None = None
    model: str | None = None

    previous_response_id: str | None = None
    instructions: str | None = None
    output: list[OpenResponsesItem] | None = None
    error: OpenResponsesError | None = None

    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    truncation: str | None = None
    parallel_tool_calls: bool | None = None
    text: dict[str, Any] | None = None
    top_p: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    top_logprobs: int | None = None
    temperature: float | None = None
    reasoning: dict[str, Any] | None = None
    usage: OpenResponsesUsage | None = None
    max_output_tokens: int | None = None
    max_tool_calls: int | None = None
    store: bool | None = None
    background: bool | None = None
    service_tier: str | None = None
    metadata: dict[str, Any] | None = None
    safety_identifier: str | None = None
    prompt_cache_key: str | None = None
    incomplete_details: dict[str, Any] | None = None


class OpenResponsesStreamEvent(BaseModel):
    """
    Typed semantic stream event for Open Responses SSE payloads.

    The event payload shape varies by event type; unknown fields are preserved.
    """

    model_config = ConfigDict(extra="allow")

    type: str
    sequence_number: int | None = None
    response: OpenResponsesResponse | None = None
    error: OpenResponsesError | None = None
