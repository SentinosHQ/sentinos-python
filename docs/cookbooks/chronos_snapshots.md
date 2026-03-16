## Chronos snapshots

```python
from sentinos import SentinosClient

client = SentinosClient.from_env()

created = client.chronos.create_snapshot(
    anchors=["node:customer:123"],
    depth=2,
    include_decision_traces=True,
)

snap = client.chronos.get_snapshot(snapshot_id=created.snapshot_id)
print(len(snap.nodes or []), len(snap.edges or []))
```

Set `SENTINOS_CHRONOS_URL` if Chronos is hosted on a different endpoint than the base URL.
