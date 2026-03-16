## Quickstart

Install from PyPI:

```bash
pip install sentinos
```

Configure the SDK through environment variables to stick to the canonical onboarding path:

```bash
export SENTINOS_BASE_URL="https://api.sentinos.ai"
export SENTINOS_ORG_ID="<org-id>"  # alias: TENANT_ID is still supported
export SENTINOS_ACCESS_TOKEN="<access-token>"
```

Use `SentinosClient.from_env()` to build the client and make calls:

```python
from sentinos import SentinosClient

client = SentinosClient.from_env()
trace = client.kernel.execute(
    agent_id="agent1",
    session_id="sess-1",
    intent={"type": "tool_call", "tool": "example.tool", "args": {"x": 1}},
)
print(trace.decision)
```

If you host parts of the stack separately, override `SENTINOS_KERNEL_URL`, `SENTINOS_ARBITER_URL`, or `SENTINOS_CHRONOS_URL` rather than switching constructors.
