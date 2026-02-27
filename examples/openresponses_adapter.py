from __future__ import annotations

from sentinos import LLMGuard, SentinosClient, create_openresponses_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="assistant-1", session_id="sess-openresponses-1")

# `openai_client` can point at any Open Responses-compatible provider base URL.
adapter = create_openresponses_adapter(guard=guard, client=openai_client)
result = adapter.create(
    model="gpt-4.1-mini",
    input=[
        {
            "type": "message",
            "role": "user",
            "content": "Generate a compliance-safe incident summary.",
        }
    ],
    tools=[
        {
            "type": "function",
            "name": "lookup_incident",
            "description": "Fetch incident details by incident ID",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        }
    ],
    tool_choice="auto",
    metadata={"workflow": "incident-summary"},
)

print(result.trace.trace_id, result.trace.decision, result.response.id, result.response.status)
