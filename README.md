# sentinos (Python SDK)

[![PyPI](https://img.shields.io/pypi/v/sentinos.svg?cacheSeconds=300)](https://pypi.org/project/sentinos/)
[![Python](https://img.shields.io/pypi/pyversions/sentinos.svg)](https://pypi.org/project/sentinos/)
[![CI](https://github.com/SentinosHQ/sentinos-python/actions/workflows/ci.yml/badge.svg)](https://github.com/SentinosHQ/sentinos-python/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/sentinos.svg)](LICENSE)

Sentinos is the control plane for AI agents: runtime governance, deterministic policy outcomes, and trace-backed forensics.

This package is the high-level Python SDK for Sentinos. It wraps `sentinos-sdk-core` with ergonomic clients and adapters for:

- Kernel (execution boundary, autonomy sessions, escalations, traces)
- Arbiter (policy lifecycle + deterministic outcomes)
- Chronos (context snapshots and provenance)
- Alerts, incidents, marketplace, and supporting workflows

## Install

```bash
pip install sentinos
```

Optional extras:

```bash
pip install "sentinos[providers]"  # openai + anthropic + boto3 (bedrock)
pip install "sentinos[otel]"       # OpenTelemetry helpers
pip install "sentinos[langchain]"  # LangChain integration helpers
pip install "sentinos[grpc]"       # grpcio + protobuf support
```

## Configure

Recommended environment setup:

```bash
export SENTINOS_BASE_URL="https://<your-sentinos-api-host>"
export SENTINOS_ORG_ID="<org-id>"
export SENTINOS_ACCESS_TOKEN="<access-token>"
```

Notes:

- `SENTINOS_ORG_ID` is preferred; `SENTINOS_TENANT_ID` is supported as an alias.
- If services are hosted separately, set `SENTINOS_KERNEL_URL`, `SENTINOS_ARBITER_URL`, and `SENTINOS_CHRONOS_URL`.

## Quickstart

```python
from sentinos import SentinosClient

client = SentinosClient.from_env()
print(client.kernel.get_runtime_metrics())
print(client.arbiter.governance_dashboard())
```

Explicit constructor:

```python
from sentinos import SentinosClient
from sentinos.auth.jwt import JWTAuth

client = SentinosClient.simple(
    base_url="https://<your-sentinos-api-host>",
    org_id="acme",
    auth=JWTAuth(lambda: "<access-token>"),
)
print(client.kernel.get_runtime_metrics())
```

## LLM Governance Integration

```python
from sentinos import LLMGuard, SentinosClient

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="assistant-1", session_id="sess-123")

result = guard.run(
    provider="openai",
    operation="chat.completions",
    model="gpt-4o-mini",
    request={"messages": [{"role": "user", "content": "Summarize this incident"}]},
    invoke=lambda: {"id": "resp-1", "model": "gpt-4o-mini"},
)
print(result.trace.trace_id, result.trace.decision)
```

OpenAI-compatible Responses API adapter:

```python
from sentinos import LLMGuard, SentinosClient, create_openresponses_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="assistant-1", session_id="sess-openresponses-1")
adapter = create_openresponses_adapter(guard=guard, client=openai_client)
result = adapter.create(
    model="gpt-4.1-mini",
    input=[{"type": "message", "role": "user", "content": "summarize recent incidents"}],
)
print(result.trace.trace_id, result.trace.decision, result.response.status)
```

## Workforce Auth (Enterprise)

```python
from sentinos import SentinosClient, WorkforceAssertion, WorkforceTokenProvider
from sentinos.auth.jwt import JWTAuth

workforce_provider = WorkforceTokenProvider.from_env(
    assertion_provider=lambda: WorkforceAssertion(
        external_subject="employee-123",
        email="employee@enterprise.example",
        groups=["AI_USERS"],
    ),
    idp_issuer="https://login.microsoftonline.com/tenant/v2.0",
)

client = SentinosClient(
    org_id="enterprise-org",
    base_url="https://<your-sentinos-api-host>",
    auth=JWTAuth(workforce_provider),
)
```

CLI token exchange helper:

```bash
sentinos-workforce-auth exchange \
  --controlplane-url "https://app.sentinoshq.com" \
  --org-id "<org-id>" \
  --idp-issuer "https://login.microsoftonline.com/<tenant>/v2.0" \
  --external-subject "<employee-sub>" \
  --assertion-token "<signed-idp-jwt>" \
  --audience "sentinos-workforce"
```

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
tox -q
```

## Resources

- Documentation: [https://docs.sentinoshq.com/sdk/](https://docs.sentinoshq.com/sdk/)
- Repository: [https://github.com/SentinosHQ/sentinos-python](https://github.com/SentinosHQ/sentinos-python)
- Issues: [https://github.com/SentinosHQ/sentinos-python/issues](https://github.com/SentinosHQ/sentinos-python/issues)
- Release guide: `RELEASING.md`
