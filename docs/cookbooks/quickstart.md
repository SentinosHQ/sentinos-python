## Quickstart

Install from PyPI:

```bash
pip install sentinos
```

Local dev:

```bash
docker-compose up
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/sdk-core/python
pip install -e packages/sentinos-python[dev]
```

Minimal execute:

```python
from sentinos import SentinosClient

client = SentinosClient(
    org_id="acme",  # alias: tenant_id
    api_url="http://localhost:8081",
    auth_token="<jwt>",
)

trace = client.kernel.execute(
    agent_id="agent1",
    session_id="sess-1",
    intent={"type": "tool_call", "tool": "example.tool", "args": {"x": 1}},
)
print(trace.decision)
```
