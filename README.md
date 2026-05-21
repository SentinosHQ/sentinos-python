# `sentinos` (Python SDK)

![Sentinos Python SDK](https://raw.githubusercontent.com/SentinosHQ/sentinos-node/main/assets/og-default.png)

High-level Python SDK for Sentinos. Use it to connect agent workloads to governed execution, policy-backed decisions, trace forensics, and Chronos context with one environment-driven client.

If you want the lower-level generated API client instead, install [`sentinos-sdk-core`](https://pypi.org/project/sentinos-sdk-core/). Most users should start with `sentinos`.

## Install

```bash
pip install sentinos
```

Optional extras:

```bash
pip install "sentinos[openai]"     # OpenAI provider adapters and examples
pip install "sentinos[providers]"  # OpenAI, Anthropic, and Bedrock helpers
pip install "sentinos[otel]"       # OpenTelemetry helpers
pip install "sentinos[langgraph]"  # LangGraph workflow examples
pip install "sentinos[langchain]"  # LangChain adapters
pip install "sentinos[agents]"     # OpenAI Agents SDK examples
pip install "sentinos[grpc]"       # Native gRPC example support
```

## Start here

Set the standard environment variables once:

```bash
export SENTINOS_BASE_URL="https://api.sentinos.ai"
export SENTINOS_ORG_ID="<org-id>"
export SENTINOS_ACCESS_TOKEN="<access-token>"
```

Then create the client and make a governed call:

```python
from sentinos import SentinosClient

client = SentinosClient.from_env()
trace = client.kernel.execute(
    agent_id="assistant-1",
    session_id="sess-1",
    intent={"type": "tool_call", "tool": "example.tool", "args": {"x": 1}},
)

print(trace.decision, trace.trace_id)
```

If you host services separately, override `SENTINOS_KERNEL_URL`, `SENTINOS_ARBITER_URL`, or `SENTINOS_CHRONOS_URL` instead of switching constructors.

## Common workflows

- Govern direct provider calls with `LLMGuard`
- Replay and export trace evidence for audits
- Simulate Arbiter policy changes before rollout
- Pull Chronos snapshots for context-aware investigation

### LLMGuard example

```python
from sentinos import LLMGuard, SentinosClient

client = SentinosClient.from_env()
guard = LLMGuard(kernel=client.kernel, agent_id="assistant-1", session_id="sess-42")

result = guard.run(
    provider="openai",
    operation="chat.completions",
    model="gpt-4o-mini",
    request={"messages": [{"role": "user", "content": "Summarize the incident."}]},
    invoke=lambda: {"id": "resp-1", "model": "gpt-4o-mini"},
)

print(result.trace.trace_id, result.trace.decision)
```

`LLMGuard` and provider adapters attach an operator-safe `metadata.agent_rationale`
envelope before execution. The envelope is derived from runtime context such as
provider, model, operation, tool, workflow metadata, and optional concise
rationale fields. It is not hidden chain-of-thought capture; forbidden hidden or
raw fields are dropped before trace persistence.

Runnable examples include:

- `examples/openai_governed_tool_calling.py`
- `examples/openai_agents_governed_tools.py`
- `examples/langgraph_governed_workflow.py`
- `examples/x402_governed_agent_payment.py`

Validation:

```bash
PYTHONPATH=. python -m pytest
```

### Trace replay example

```python
from sentinos import SentinosClient

client = SentinosClient.from_env()
replay = client.traces.replay_trace(
    "11111111-1111-1111-1111-111111111111",
    request={"include_explain": True},
)

print(replay.decision, replay.fidelity)
```

## Enterprise auth

Workforce token exchange is available when you need employee-scoped access:

```python
from sentinos import SentinosClient, WorkforceAssertion, WorkforceTokenProvider
from sentinos.auth.jwt import JWTAuth

workforce_provider = WorkforceTokenProvider.from_env(
    assertion_provider=lambda: WorkforceAssertion(
        external_subject="employee-123",
        email="employee@enterprise.example",
        groups=["ai-users"],
    )
)

client = SentinosClient.from_env(auth=JWTAuth(workforce_provider))
```

## Docs & examples

- [Sentinos SDK docs](https://docs.sentinoshq.com/sdk/)
- [PyPI package](https://pypi.org/project/sentinos/)
- [Low-level generated client (`sentinos-sdk-core`)](https://pypi.org/project/sentinos-sdk-core/)

Included example files:

- `examples/quickstart.py`
- `examples/auth_api_key.py`
- `examples/protocols/grpc_execute_smoke.py`
- `docs/cookbooks/quickstart.md`
- `docs/cookbooks/chronos_snapshots.md`
- `docs/cookbooks/policy_simulation.md`
