# Live E2E Suite (OpenAI + Sentinos Governance)

This example suite runs a multi-stage, live, end-to-end validation of Sentinos with real OpenAI traffic and console-observable outcomes.

Stages:

1. `stage_00_bootstrap_account.py` (optional): create/login a new controlplane account and emit token exports.
2. `stage_01_setup.py`: upsert/promote governance policy + create channels/rules.
3. `stage_02_openai_traffic.py`: generate real OpenAI calls through `LLMGuard`.
4. `stage_03_triage.py`: triage alerts/anomalies, handle escalations, run incident lifecycle.
5. `stage_04_verify.py`: pull evidence surfaces (traces, reports, exports, health).
6. `run_full_live_e2e.py`: orchestrate stages.

Artifacts are written to `examples/live_e2e/artifacts/<run_id>/`.

## Install

```bash
cd /Users/gtomberlin/Documents/Code/Sentinos/packages/sentinos-python
python3 -m venv .venv-live-e2e && source .venv-live-e2e/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e ../sdk-core/python
pip install -e ".[dev,providers]"
```

If editable install for `sdk-core` fails in your current Python environment, use:

```bash
pip install ../sdk-core/python
pip install -e ".[dev,providers]"
```

## Option A: Existing token mode (fastest)

```bash
export SENTINOS_E2E_AUTH_MODE=token
export SENTINOS_ORG_ID="<org-id>"  # alias: SENTINOS_TENANT_ID
export SENTINOS_ACCESS_TOKEN="<jwt-access-token>"
export OPENAI_API_KEY="<openai-key>"
python examples/live_e2e/run_full_live_e2e.py
```

To avoid manually rotating tokens for repeated runs, you can also set bootstrap credentials.
When present, the suite will auto-login and mint a fresh access token at runtime.
If login fails with invalid credentials, it will attempt register-once fallback with the same email/password:

```bash
export SENTINOS_BOOTSTRAP_EMAIL="live-e2e@example.com"
export SENTINOS_BOOTSTRAP_PASSWORD="StrongPassword!123"
# Optional toggle (default true): export SENTINOS_E2E_AUTO_REFRESH_TOKEN=true
```

## Option B: Bootstrap a new account first

```bash
export SENTINOS_E2E_AUTH_MODE=bootstrap
export SENTINOS_CONTROLPLANE_URL="http://localhost:18084"
export SENTINOS_BOOTSTRAP_EMAIL="live-e2e@example.com"
export SENTINOS_BOOTSTRAP_PASSWORD="StrongPassword!123"
# Optional but recommended when this email already belongs to multiple orgs:
# export SENTINOS_ORG_ID="<org-id-you-want-to-target>"  # alias: SENTINOS_TENANT_ID
python examples/live_e2e/stage_00_bootstrap_account.py
```

Then use the printed exports and run:

```bash
export OPENAI_API_KEY="<openai-key>"
python examples/live_e2e/run_full_live_e2e.py
```

## Option C: Workforce mode

```bash
export SENTINOS_E2E_AUTH_MODE=workforce
export SENTINOS_CONTROLPLANE_URL="http://localhost:18084"
export SENTINOS_WORKFORCE_ORG_ID="<org-id>"
export SENTINOS_WORKFORCE_IDP_ISSUER="https://login.microsoftonline.com/<tenant>/v2.0"
export SENTINOS_WORKFORCE_EXTERNAL_SUBJECT="employee-123"
export SENTINOS_WORKFORCE_EMAIL="employee@example.com"
export SENTINOS_WORKFORCE_GROUPS="AI_USERS,FINANCE"
export SENTINOS_WORKFORCE_ASSERTION_TOKEN="<signed-idp-jwt>"  # recommended/required in hardened envs
export OPENAI_API_KEY="<openai-key>"
python examples/live_e2e/run_full_live_e2e.py
```

## Useful knobs

- `SENTINOS_KERNEL_URL` (default `http://localhost:8081`)
- `SENTINOS_ARBITER_URL` (default `http://localhost:8082`)
- `SENTINOS_CHRONOS_URL` (default `http://localhost:8083`)
- `SENTINOS_CONSOLE_URL` (default `http://localhost:3000`)
- `SENTINOS_E2E_OPENAI_MODEL` (default `gpt-4o-mini`)
- `SENTINOS_E2E_OPENAI_BASE_URL` (optional OpenAI-compatible endpoint override)
- `OPENAI_PROJECT_ID` / `OPENAI_PROJECT` (recommended for project-scoped API billing)
- `OPENAI_ORG_ID` / `OPENAI_ORGANIZATION` (optional org scoping)
- `SENTINOS_E2E_RUN_ID` (default timestamp)
- `SENTINOS_E2E_STRICT_EXPECTATIONS=true` (fail run on decision mismatches)
- `SENTINOS_E2E_DATADOG_API_KEY` (optional; enables Datadog export check)
- `SENTINOS_E2E_AUTO_REFRESH_TOKEN=true|false` (default `true` when bootstrap creds are set)

## OpenAI quota troubleshooting

If Stage 02 returns `insufficient_quota` (429), this is usually key/project scoping:

1. Ensure the key belongs to a project with active API billing.
2. Export `OPENAI_PROJECT_ID` (or `OPENAI_PROJECT`) for that project.
3. Optionally set `OPENAI_ORG_ID` if your account spans multiple orgs.
4. Re-run the suite.

## Stage-by-stage execution

```bash
python examples/live_e2e/stage_01_setup.py
python examples/live_e2e/stage_02_openai_traffic.py
python examples/live_e2e/stage_03_triage.py
python examples/live_e2e/stage_04_verify.py
```

## Import Troubleshooting

If `ModuleNotFoundError: No module named 'sentinos'` appears:

1. Ensure pip/install is bound to the same interpreter:

```bash
which python
python -m pip -V
python -c "import sys; print(sys.executable)"
```

2. Reinstall with interpreter-bound pip:

```bash
python -m pip install -e ../sdk-core/python
python -m pip install -e ".[dev,providers]"
```

3. As a direct source fallback, run with:

```bash
PYTHONPATH=/Users/gtomberlin/Documents/Code/Sentinos/packages/sentinos-python \
python examples/live_e2e/run_full_live_e2e.py
```

## Expected console checks

- `#traces`: ALLOW/SHADOW/ESCALATE/DENY traces for the same run/agent/session.
- `#alerts`: firing/escalated/resolved alerts tied to live policy outcomes.
- `#incidents`: incident created and resolved with timeline events.
- `#kernel`: escalation inbox/session updates.
- `#analytics` and `#dashboard`: aggregate decision and risk trends.
- `#workforce` (if workforce mode): subject/session visibility.
