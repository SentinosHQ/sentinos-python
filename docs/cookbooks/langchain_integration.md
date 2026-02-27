## LangChain integration (governed tool/runtime pattern)

This cookbook shows how to route LangChain tool invocations through Sentinos before execution.

## Why this pattern

Sentinos is the policy and observability control plane. In most LangChain deployments, your application
still executes provider and tool calls directly. Use Sentinos to gate those calls and persist decision traces.

## Install

```bash
pip install "sentinos[langchain]"
```

## Pattern

1. Build `SentinosClient`
2. Create `LLMGuard` with `agent_id` and `session_id`
3. In each tool callback:
   1. call `guard.authorize(...)`
   2. if decision is `ALLOW` or `SHADOW`, execute underlying tool
   3. call `guard.record_response(...)`

## Example

```python
from sentinos import LLMGuard, SentinosClient, make_guarded_tool

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="agent1", session_id="sess-1")

def guarded_tool(tool_name: str, tool_args: dict) -> dict:
    trace = guard.authorize(
        provider="tool-runtime",
        operation="invoke",
        request={"tool": tool_name, "args": tool_args},
        tool_name=f"tool.{tool_name}",
    )
    if trace.decision not in {"ALLOW", "SHADOW"}:
        return {
            "trace_id": trace.trace_id,
            "decision": trace.decision,
            "reason": trace.policy_evaluation.reason,
        }

    # Call your real tool executor here.
    tool_result = {"ok": True, "echo": tool_args}

    guard.record_response(
        provider="tool-runtime",
        operation=tool_name,
        trace=trace,
        response=tool_result,
    )
    return {
        "trace_id": trace.trace_id,
        "decision": trace.decision,
        "result": tool_result,
    }
```

For thin wrapper mode, use:

```python
from sentinos import make_guarded_tool

guarded_refund = make_guarded_tool(
    guard=guard,
    tool_name="stripe.refund",
    execute=lambda **kwargs: {"ok": True, "forwarded": kwargs},
)
```

## Notes

- `skip_connector=true` is set by guard metadata, so Kernel authorizes and traces without invoking built-in connector mocks.
- This keeps governance centralized while letting your runtime use any LLM/provider SDK.
- For full docs, see https://docs.sentinoshq.com/sdk/
