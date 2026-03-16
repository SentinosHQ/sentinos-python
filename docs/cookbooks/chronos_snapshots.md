## Chronos snapshots

```python
from sentinos import SentinosClient

client = SentinosClient(
    org_id="acme",  # alias: tenant_id
    api_url="https://api.sentinos.ai",
    # override only when Chronos is intentionally hosted on a different endpoint.
    # chronos_url="https://chronos.sentinos.ai",
    auth_token="<jwt>",
)

created = client.chronos.create_snapshot(
    anchors=["node:customer:123"],
    depth=2,
    include_decision_traces=True,
)

snap = client.chronos.get_snapshot(snapshot_id=created.snapshot_id)
print(len(snap.nodes or []), len(snap.edges or []))
```
