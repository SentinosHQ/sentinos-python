"""Shared helpers for live end-to-end Sentinos SDK demonstrations."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import string
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from sentinos import SentinosClient, WorkforceAssertion, WorkforceTokenProvider
    from sentinos.auth.jwt import JWTAuth
except ModuleNotFoundError:
    # Allow running examples directly from source checkout without an installed wheel.
    import sys

    package_root = Path(__file__).resolve().parents[2]
    sdk_core_root = Path(__file__).resolve().parents[3] / "sdk-core" / "python"
    for path in (package_root, sdk_core_root):
        p = str(path)
        if p not in sys.path:
            sys.path.insert(0, p)
    from sentinos import SentinosClient, WorkforceAssertion, WorkforceTokenProvider
    from sentinos.auth.jwt import JWTAuth


class LiveE2EError(RuntimeError):
    """Raised when live E2E configuration or execution fails."""


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _sanitize_token(value: str) -> str:
    lowered = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return lowered or "run"


def _rego_package_from_policy_id(policy_id: str) -> str:
    """
    Mirror Arbiter's policyEntrypointRef package convention:
    package sentinos.<sanitized policy_id with '/' -> '.'>
    """
    raw = (policy_id or "").strip().replace("/", ".")
    parts = raw.split(".")
    normalized: list[str] = []
    allowed = set(string.ascii_letters + string.digits + "_")
    for part in parts:
        segment_chars = [ch if ch in allowed else "_" for ch in part]
        segment = "".join(segment_chars) or "_"
        if segment[0].isdigit():
            segment = "_" + segment
        normalized.append(segment)
    return "sentinos." + ".".join(normalized)


def _utc_now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


def iso_utc(ts: dt.datetime | None = None) -> str:
    out = (ts or _utc_now()).astimezone(dt.timezone.utc)
    return out.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_utc_minus(minutes: int) -> str:
    return iso_utc(_utc_now() - dt.timedelta(minutes=minutes))


def _csv_env(name: str) -> list[str]:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _json_default(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "model_dump") and callable(getattr(value, "model_dump")):
        return value.model_dump(mode="json")
    if isinstance(value, set):
        return sorted(value)
    return str(value)


def _post_json(url: str, body: dict[str, Any], token: str | None = None, timeout_seconds: float = 15.0) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    if token:
        req.add_header("authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise LiveE2EError(f"Unexpected non-object JSON response from {url}")
            return payload
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = ""
        raise LiveE2EError(f"HTTP {exc.code} from {url}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise LiveE2EError(f"Network error calling {url}: {exc}") from exc


@dataclass
class LiveE2EConfig:
    run_id: str
    tenant_id: str | None
    kernel_url: str
    arbiter_url: str
    chronos_url: str
    controlplane_url: str
    console_url: str
    auth_mode: str
    access_token: str | None
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str | None
    openai_org_id: str | None
    openai_project_id: str | None
    policy_id: str
    policy_version: str
    policy_package: str
    target_tool: str
    agent_id: str
    session_id: str
    artifacts_dir: Path
    strict_expectations: bool
    bootstrap_email: str | None
    bootstrap_password: str | None
    bootstrap_display_name: str | None
    workforce_org_id: str | None
    workforce_idp_issuer: str | None
    workforce_external_subject: str | None
    workforce_email: str | None
    workforce_display_name: str | None
    workforce_groups: list[str]
    workforce_assertion_token: str | None
    workforce_token_binding_value: str | None
    workforce_device_id: str | None
    workforce_audience: str | None
    workforce_requested_ttl_minutes: int | None
    auto_refresh_token_with_bootstrap: bool


def load_config(*, require_openai_key: bool) -> LiveE2EConfig:
    now = _utc_now()
    run_id_env = (os.getenv("SENTINOS_E2E_RUN_ID") or "").strip()
    run_id = _sanitize_token(run_id_env or now.strftime("%Y%m%d-%H%M%S"))
    suffix = run_id[:20]

    kernel_url = (os.getenv("SENTINOS_KERNEL_URL") or "http://localhost:8081").strip()
    arbiter_url = (os.getenv("SENTINOS_ARBITER_URL") or "http://localhost:8082").strip()
    chronos_url = (os.getenv("SENTINOS_CHRONOS_URL") or "http://localhost:8083").strip()
    controlplane_url = (os.getenv("SENTINOS_CONTROLPLANE_URL") or "http://localhost:18084").strip()
    console_url = (os.getenv("SENTINOS_CONSOLE_URL") or "http://localhost:3000").strip()
    # Prefer org_id naming for acquisition-readiness DX, but keep tenant_id as the
    # stable internal field name across services/SDKs.
    tenant_id = (os.getenv("SENTINOS_ORG_ID") or os.getenv("SENTINOS_TENANT_ID") or "").strip() or None
    access_token = (os.getenv("SENTINOS_ACCESS_TOKEN") or "").strip() or None

    openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or None
    if require_openai_key and not openai_api_key:
        raise LiveE2EError("OPENAI_API_KEY is required for live OpenAI traffic stages")

    openai_model = (os.getenv("SENTINOS_E2E_OPENAI_MODEL") or "gpt-4o-mini").strip()
    openai_base_url = (os.getenv("SENTINOS_E2E_OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "").strip() or None
    openai_org_id = (os.getenv("OPENAI_ORG_ID") or os.getenv("OPENAI_ORGANIZATION") or "").strip() or None
    openai_project_id = (os.getenv("OPENAI_PROJECT_ID") or os.getenv("OPENAI_PROJECT") or "").strip() or None
    target_tool = "llm.openai.chat.completions"
    policy_id = (os.getenv("SENTINOS_E2E_POLICY_ID") or f"sentinos/live-e2e/openai-governance-{suffix}").strip()
    policy_version = (os.getenv("SENTINOS_E2E_POLICY_VERSION") or f"v1.0.{now.strftime('%Y%m%d%H%M%S')}").strip()
    policy_package = _rego_package_from_policy_id(policy_id)
    agent_id = (os.getenv("SENTINOS_E2E_AGENT_ID") or f"live-e2e-agent-{suffix}").strip()
    session_id = (os.getenv("SENTINOS_E2E_SESSION_ID") or f"live-e2e-session-{suffix}").strip()
    strict_expectations = _truthy(os.getenv("SENTINOS_E2E_STRICT_EXPECTATIONS"))

    artifacts_root = (os.getenv("SENTINOS_E2E_ARTIFACTS_DIR") or "").strip()
    artifacts_dir = Path(artifacts_root) if artifacts_root else (Path(__file__).resolve().parent / "artifacts" / run_id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    bootstrap_email = (os.getenv("SENTINOS_BOOTSTRAP_EMAIL") or "").strip() or None
    bootstrap_password = (os.getenv("SENTINOS_BOOTSTRAP_PASSWORD") or "").strip() or None
    bootstrap_display_name = (os.getenv("SENTINOS_BOOTSTRAP_DISPLAY_NAME") or "Sentinos Live E2E").strip() or None

    workforce_org_id = (os.getenv("SENTINOS_WORKFORCE_ORG_ID") or "").strip() or None
    workforce_idp_issuer = (os.getenv("SENTINOS_WORKFORCE_IDP_ISSUER") or "").strip() or None
    workforce_external_subject = (os.getenv("SENTINOS_WORKFORCE_EXTERNAL_SUBJECT") or "").strip() or None
    workforce_email = (os.getenv("SENTINOS_WORKFORCE_EMAIL") or "").strip() or None
    workforce_display_name = (os.getenv("SENTINOS_WORKFORCE_DISPLAY_NAME") or "").strip() or None
    workforce_groups = _csv_env("SENTINOS_WORKFORCE_GROUPS")
    workforce_assertion_token = (os.getenv("SENTINOS_WORKFORCE_ASSERTION_TOKEN") or "").strip() or None
    workforce_token_binding_value = (os.getenv("SENTINOS_WORKFORCE_TOKEN_BINDING_VALUE") or "").strip() or None
    workforce_device_id = (os.getenv("SENTINOS_WORKFORCE_DEVICE_ID") or "").strip() or None
    workforce_audience = (os.getenv("SENTINOS_WORKFORCE_EXCHANGE_AUDIENCE") or "").strip() or None
    ttl_raw = (os.getenv("SENTINOS_WORKFORCE_REQUESTED_TTL_MINUTES") or "").strip()
    workforce_requested_ttl_minutes = int(ttl_raw) if ttl_raw else None
    auto_refresh_raw = (os.getenv("SENTINOS_E2E_AUTO_REFRESH_TOKEN") or "").strip()
    auto_refresh_token_with_bootstrap = True if not auto_refresh_raw else _truthy(auto_refresh_raw)

    auth_mode = (os.getenv("SENTINOS_E2E_AUTH_MODE") or "").strip().lower()
    if not auth_mode:
        if access_token:
            auth_mode = "token"
        elif workforce_external_subject and workforce_idp_issuer and (workforce_org_id or tenant_id):
            auth_mode = "workforce"
        elif bootstrap_email and bootstrap_password:
            auth_mode = "bootstrap"
        else:
            auth_mode = "token"

    if auth_mode not in {"token", "workforce", "bootstrap"}:
        raise LiveE2EError("SENTINOS_E2E_AUTH_MODE must be one of: token, workforce, bootstrap")

    if auth_mode == "token":
        has_bootstrap_credentials = bool(bootstrap_email and bootstrap_password)
        if not access_token and not has_bootstrap_credentials:
            raise LiveE2EError(
                "SENTINOS_ACCESS_TOKEN is required for token auth mode unless "
                "SENTINOS_BOOTSTRAP_EMAIL/SENTINOS_BOOTSTRAP_PASSWORD are set for auto auth."
            )
        if not tenant_id and not has_bootstrap_credentials:
            raise LiveE2EError(
                "SENTINOS_ORG_ID (alias: SENTINOS_TENANT_ID) is required for token auth mode unless "
                "SENTINOS_BOOTSTRAP_EMAIL/SENTINOS_BOOTSTRAP_PASSWORD are set for auto auth."
            )
    elif auth_mode == "bootstrap":
        if not bootstrap_email or not bootstrap_password:
            raise LiveE2EError("SENTINOS_BOOTSTRAP_EMAIL and SENTINOS_BOOTSTRAP_PASSWORD are required for bootstrap mode")
    elif auth_mode == "workforce":
        if not workforce_idp_issuer or not workforce_external_subject:
            raise LiveE2EError(
                "SENTINOS_WORKFORCE_IDP_ISSUER and SENTINOS_WORKFORCE_EXTERNAL_SUBJECT are required for workforce mode"
            )
        if not (workforce_org_id or tenant_id):
            raise LiveE2EError(
                "SENTINOS_WORKFORCE_ORG_ID or SENTINOS_ORG_ID (alias: SENTINOS_TENANT_ID) is required for workforce mode"
            )
        if not controlplane_url:
            raise LiveE2EError("SENTINOS_CONTROLPLANE_URL is required for workforce mode")

    return LiveE2EConfig(
        run_id=run_id,
        tenant_id=tenant_id,
        kernel_url=kernel_url,
        arbiter_url=arbiter_url,
        chronos_url=chronos_url,
        controlplane_url=controlplane_url,
        console_url=console_url,
        auth_mode=auth_mode,
        access_token=access_token,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=openai_base_url,
        openai_org_id=openai_org_id,
        openai_project_id=openai_project_id,
        policy_id=policy_id,
        policy_version=policy_version,
        policy_package=policy_package,
        target_tool=target_tool,
        agent_id=agent_id,
        session_id=session_id,
        artifacts_dir=artifacts_dir,
        strict_expectations=strict_expectations,
        bootstrap_email=bootstrap_email,
        bootstrap_password=bootstrap_password,
        bootstrap_display_name=bootstrap_display_name,
        workforce_org_id=workforce_org_id,
        workforce_idp_issuer=workforce_idp_issuer,
        workforce_external_subject=workforce_external_subject,
        workforce_email=workforce_email,
        workforce_display_name=workforce_display_name,
        workforce_groups=workforce_groups,
        workforce_assertion_token=workforce_assertion_token,
        workforce_token_binding_value=workforce_token_binding_value,
        workforce_device_id=workforce_device_id,
        workforce_audience=workforce_audience,
        workforce_requested_ttl_minutes=workforce_requested_ttl_minutes,
        auto_refresh_token_with_bootstrap=auto_refresh_token_with_bootstrap,
    )


def info(message: str) -> None:
    print(f"[{iso_utc()}] {message}")


def write_artifact(config: LiveE2EConfig, name: str, payload: dict[str, Any]) -> Path:
    path = config.artifacts_dir / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    return path


def load_state(config: LiveE2EConfig) -> dict[str, Any]:
    path = config.artifacts_dir / "state.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return raw


def save_state(config: LiveE2EConfig, state: dict[str, Any]) -> Path:
    path = config.artifacts_dir / "state.json"
    path.write_text(json.dumps(state, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    return path


def bootstrap_account_if_needed(config: LiveE2EConfig) -> dict[str, Any] | None:
    if config.auth_mode != "bootstrap":
        return None
    if config.access_token and config.tenant_id:
        return {"mode": "bootstrap", "status": "using_existing_token", "tenant_id": config.tenant_id}

    if not config.bootstrap_email or not config.bootstrap_password:
        raise LiveE2EError("Bootstrap auth mode requires bootstrap email/password")

    register_payload = {
        "email": config.bootstrap_email,
        "password": config.bootstrap_password,
        "display_name": config.bootstrap_display_name or "Sentinos Live E2E",
    }
    register_url = f"{config.controlplane_url.rstrip('/')}/v1/auth/register"
    login_url = f"{config.controlplane_url.rstrip('/')}/v1/auth/login/password"

    try:
        response = _post_json(register_url, register_payload)
        action = "registered"
    except LiveE2EError as exc:
        if "HTTP 409" not in str(exc):
            raise
        login_payload: dict[str, Any] = {
            "email": config.bootstrap_email,
            "password": config.bootstrap_password,
        }
        preferred_org_id = (config.tenant_id or config.workforce_org_id or "").strip()
        if preferred_org_id:
            login_payload["org_id"] = preferred_org_id
        response = _post_json(
            login_url,
            login_payload,
        )
        action = "logged_in_existing"

    tokens = response.get("tokens")
    if not isinstance(tokens, dict):
        raise LiveE2EError("Controlplane auth response missing tokens object")
    access_token = str(tokens.get("access_token") or "").strip()
    tenant_id = str(tokens.get("tenant_id") or tokens.get("org_id") or "").strip()
    if not access_token or not tenant_id:
        raise LiveE2EError("Controlplane auth response missing access_token or tenant_id")

    config.access_token = access_token
    config.tenant_id = tenant_id
    return {
        "mode": "bootstrap",
        "action": action,
        "tenant_id": tenant_id,
        "org_id": tokens.get("org_id"),
        "membership_id": tokens.get("membership_id"),
        "roles": tokens.get("roles") or [],
        "permissions": tokens.get("permissions") or [],
    }


def refresh_access_token_with_bootstrap_credentials(config: LiveE2EConfig) -> dict[str, Any] | None:
    """
    Refresh access token using controlplane password login when bootstrap credentials are available.

    This lets repeated live E2E runs avoid manual token minting and prevents stale/legacy token failures.
    """
    if not config.auto_refresh_token_with_bootstrap:
        return None
    if not config.bootstrap_email or not config.bootstrap_password:
        return None
    login_url = f"{config.controlplane_url.rstrip('/')}/v1/auth/login/password"
    payload: dict[str, Any] = {
        "email": config.bootstrap_email,
        "password": config.bootstrap_password,
    }
    preferred_org_id = (config.tenant_id or config.workforce_org_id or "").strip()
    if preferred_org_id:
        payload["org_id"] = preferred_org_id
    def apply_tokens(tokens: dict[str, Any], *, source: str) -> dict[str, Any]:
        access_token = str(tokens.get("access_token") or "").strip()
        tenant_id = str(tokens.get("tenant_id") or tokens.get("org_id") or "").strip()
        if not access_token or not tenant_id:
            raise LiveE2EError("missing access_token or tenant_id")
        previous_tenant = (config.tenant_id or "").strip()
        config.access_token = access_token
        config.tenant_id = tenant_id
        if previous_tenant and previous_tenant != tenant_id:
            info(
                f"Auto auth switched tenant context from {previous_tenant} to {tenant_id} "
                f"(source={source}); update SENTINOS_ORG_ID (or SENTINOS_TENANT_ID) if needed."
            )
        return {
            "mode": "auto_refresh",
            "status": "ok",
            "source": source,
            "tenant_id": tenant_id,
            "org_id": tokens.get("org_id"),
            "membership_id": tokens.get("membership_id"),
            "roles": tokens.get("roles") or [],
            "permissions": tokens.get("permissions") or [],
        }

    try:
        login_response = _post_json(login_url, payload)
        login_tokens = login_response.get("tokens")
        if not isinstance(login_tokens, dict):
            raise LiveE2EError("auth response missing tokens object")
        return apply_tokens(login_tokens, source="login")
    except LiveE2EError as exc:
        msg = str(exc).lower()
        if "invalid credentials" not in msg:
            info(f"Auto token refresh skipped (password login failed): {exc}")
            return {"mode": "auto_refresh", "status": "failed", "error": str(exc)}
        info(f"Auto token refresh login failed with invalid credentials, attempting register fallback: {exc}")

    register_url = f"{config.controlplane_url.rstrip('/')}/v1/auth/register"
    register_payload = {
        "email": config.bootstrap_email,
        "password": config.bootstrap_password,
        "display_name": config.bootstrap_display_name or "Sentinos Live E2E",
    }
    try:
        register_response = _post_json(register_url, register_payload)
    except LiveE2EError as exc:
        info(f"Auto token refresh skipped (register fallback failed): {exc}")
        return {"mode": "auto_refresh", "status": "failed", "error": str(exc)}

    register_tokens = register_response.get("tokens")
    if not isinstance(register_tokens, dict):
        info("Auto token refresh skipped (register response missing tokens object)")
        return {"mode": "auto_refresh", "status": "failed", "error": "missing tokens in register response"}

    try:
        return apply_tokens(register_tokens, source="register")
    except LiveE2EError as exc:
        info(f"Auto token refresh skipped (register token parsing failed): {exc}")
        return {"mode": "auto_refresh", "status": "failed", "error": str(exc)}


def build_sentinos_client(config: LiveE2EConfig) -> SentinosClient:
    refresh_access_token_with_bootstrap_credentials(config)
    bootstrap_account_if_needed(config)

    tenant_id = (config.tenant_id or "").strip() or None
    if config.auth_mode in {"token", "bootstrap"}:
        if not config.access_token:
            raise LiveE2EError("No access token available for Sentinos client initialization")
        if not tenant_id:
            raise LiveE2EError("tenant_id is required for Sentinos client initialization")
        auth = JWTAuth(lambda: config.access_token or "")
        return SentinosClient(
            org_id=tenant_id,
            kernel_url=config.kernel_url,
            arbiter_url=config.arbiter_url,
            chronos_url=config.chronos_url,
            auth=auth,
        )

    if config.auth_mode != "workforce":
        raise LiveE2EError(f"Unsupported auth mode: {config.auth_mode}")

    org_id = (config.workforce_org_id or tenant_id or "").strip()
    if not org_id:
        raise LiveE2EError("workforce org_id is required")

    def assertion_provider() -> WorkforceAssertion:
        subject = (config.workforce_external_subject or "").strip()
        if not subject:
            raise LiveE2EError("workforce external subject is required")
        return WorkforceAssertion(
            external_subject=subject,
            email=config.workforce_email,
            display_name=config.workforce_display_name,
            groups=(config.workforce_groups or None),
            assertion_token=config.workforce_assertion_token,
            token_binding_value=config.workforce_token_binding_value,
            device_id=config.workforce_device_id,
        )

    provider = WorkforceTokenProvider(
        controlplane_url=config.controlplane_url,
        org_id=org_id,
        idp_issuer=config.workforce_idp_issuer or "",
        assertion_provider=assertion_provider,
        audience=config.workforce_audience,
        requested_ttl_minutes=config.workforce_requested_ttl_minutes,
    )
    config.tenant_id = org_id

    return SentinosClient(
        org_id=org_id,
        kernel_url=config.kernel_url,
        arbiter_url=config.arbiter_url,
        chronos_url=config.chronos_url,
        auth=JWTAuth(provider),
    )


def build_openai_client(config: LiveE2EConfig) -> Any:
    if not config.openai_api_key:
        raise LiveE2EError("OPENAI_API_KEY is required")
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise LiveE2EError("openai dependency is missing. Install with: pip install 'sentinos[providers]'") from exc
    kwargs: dict[str, Any] = {"api_key": config.openai_api_key}
    if config.openai_base_url:
        kwargs["base_url"] = config.openai_base_url
    if config.openai_org_id:
        kwargs["organization"] = config.openai_org_id
    if config.openai_project_id:
        kwargs["project"] = config.openai_project_id
    return OpenAI(**kwargs)
