## Quickstart

Install from PyPI:

```bash
pip install sentinos
```

Authenticate with your Sentinos workspace:

```bash
export SENTINOS_BASE_URL="https://api.sentinos.ai"
export SENTINOS_ORG_ID="<org-id>"
export SENTINOS_ACCESS_TOKEN="<access-token>"
```

Minimal execute:

```python
from sentinos import SentinosClient

client = SentinosClient(
    org_id="acme",  # alias: tenant_id
    api_url="https://api.sentinos.ai",
    auth_token="<jwt>",
)

trace = client.kernel.execute(
    agent_id="agent1",
    session_id="sess-1",
    intent={"type": "tool_call", "tool": "example.tool", "args": {"x": 1}},
)
print(trace.decision)
```
