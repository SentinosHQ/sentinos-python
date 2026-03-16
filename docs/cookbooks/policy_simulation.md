## Policy simulation

```python
from sentinos import SentinosClient

client = SentinosClient.from_env()

rego = """
package sentinos.policy

default decision := {"decision":"DENY","reason":"default deny"}
"""

client.arbiter.create_policy(policy_id="finance/refund", rego=rego, version="v1", status="draft")

sim = client.arbiter.simulate_policy(candidate_rego=rego, trace_limit=50)
print(sim.summary if hasattr(sim, "summary") else sim.to_dict())
```

Override `SENTINOS_ARBITER_URL` only if Arbiter runs on a separate host from your base URL.
