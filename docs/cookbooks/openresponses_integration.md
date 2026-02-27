## Open Responses integration (governed provider portability)

Use this cookbook when your runtime talks to a provider/router implementing the Open Responses `/responses` shape.

## Why this pattern

- One request/streaming contract across multiple providers.
- Sentinos policy enforcement before each model call.
- Decision trace + session event provenance for audits.

## Example

```python
from sentinos import LLMGuard, SentinosClient, create_openresponses_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="agent1", session_id="sess-openresponses-1")

# `provider_client` may be OpenAI-compatible or any Open Responses-compatible SDK client.
adapter = create_openresponses_adapter(guard=guard, client=provider_client)

result = adapter.create(
    model="gpt-4.1-mini",
    input=[{"type": "message", "role": "user", "content": "Draft incident summary"}],
    metadata={"workflow": "incident-summary"},
)

print(result.trace.trace_id, result.trace.decision, result.response.id, result.response.status)
```

## Streaming example

```python
streamed = adapter.stream(
    model="gpt-4.1-mini",
    input=[{"type": "message", "role": "user", "content": "Draft postmortem update"}],
)
for event in streamed.events:
    print(event.type)
```

## Notes

- `OpenResponsesAdapter` uses `LLMGuard` and `skip_connector=true` metadata to keep governance centralized.
- Deny/escalate decisions raise typed exceptions before provider execution.
- You can parse raw SSE lines with `iter_openresponses_sse_lines` when needed.
