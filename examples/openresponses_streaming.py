from __future__ import annotations

from sentinos import LLMGuard, SentinosClient, create_openresponses_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="assistant-1", session_id="sess-openresponses-stream")
adapter = create_openresponses_adapter(guard=guard, client=openai_client)

streamed = adapter.stream(
    model="gpt-4.1-mini",
    input=[{"type": "message", "role": "user", "content": "Draft a postmortem update."}],
    text={"verbosity": "medium"},
    reasoning={"effort": "medium", "summary": "auto"},
)

for event in streamed.events:
    print(event.type)

if streamed.final_response is not None:
    print(
        "final:",
        streamed.final_response.id,
        streamed.final_response.status,
        len(streamed.final_response.output or []),
    )
