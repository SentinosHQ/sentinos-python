## OpenRouter integration (governed OpenAI-compatible routing)

Use this cookbook when your runtime executes OpenRouter model calls and you want Sentinos policy enforcement + trace lineage.

## Chat/Responses adapter example

```python
from sentinos import LLMGuard, SentinosClient, create_openrouter_chat_adapter, create_openrouter_responses_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="agent1", session_id="sess-openrouter-1")

chat_adapter = create_openrouter_chat_adapter(
    guard=guard,
    api_key="<OPENROUTER_API_KEY>",
    http_referer="https://console.example.com",
    x_title="Sentinos Console",
)
chat_result = chat_adapter.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Summarize incident status"}],
)

responses_adapter = create_openrouter_responses_adapter(
    guard=guard,
    api_key="<OPENROUTER_API_KEY>",
)
responses_result = responses_adapter.create(
    model="openai/gpt-4.1-mini",
    input=[{"role": "user", "content": "Draft customer update"}],
)

print(chat_result.trace.trace_id, responses_result.trace.trace_id)
```

## Open Responses schema example

```python
from sentinos import LLMGuard, SentinosClient, create_openrouter_openresponses_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="agent1", session_id="sess-openrouter-responses")

adapter = create_openrouter_openresponses_adapter(
    guard=guard,
    api_key="<OPENROUTER_API_KEY>",
)
result = adapter.create(
    model="openai/gpt-4.1-mini",
    input=[{"type": "message", "role": "user", "content": "Create incident recap"}],
)
print(result.trace.trace_id, result.trace.decision, result.response.id)
```

## Notes

- OpenRouter helpers default to `https://openrouter.ai/api/v1`.
- API key is taken from `api_key=` or `OPENROUTER_API_KEY`.
- Policy tool naming is `llm.openrouter.<operation>` for precise governance targeting.
