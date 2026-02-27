from __future__ import annotations

import datetime as dt
import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class WorkforceTokenError(RuntimeError):
    """Base class for workforce token exchange failures."""


class WorkforcePolicyDeniedError(WorkforceTokenError):
    """Raised when organization policy denies workforce token issuance."""


class WorkforceMappingError(WorkforceTokenError):
    """Raised when group-to-role/team mappings reject or fail access."""


class WorkforceSessionRevokedError(WorkforceTokenError):
    """Raised when token refresh fails due to revocation or expiration."""


@dataclass(frozen=True)
class WorkforceAssertion:
    external_subject: str
    email: str | None = None
    display_name: str | None = None
    groups: list[str] | None = None
    assertion_token: str | None = None
    token_binding_value: str | None = None
    device_id: str | None = None


AssertionProvider = Callable[[], WorkforceAssertion]


def _iso8601_utc(value: str) -> dt.datetime:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(v)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


@dataclass
class WorkforceTokenProvider:
    """
    Dynamic bearer token provider for enterprise workforce access.

    This provider exchanges enterprise identity assertions for short-lived Sentinos
    access tokens, and refreshes them automatically when possible.
    """

    controlplane_url: str
    org_id: str
    idp_issuer: str
    assertion_provider: AssertionProvider
    audience: str | None = None
    requested_ttl_minutes: int | None = None
    timeout_seconds: float = 10.0
    refresh_skew_seconds: int = 30

    _access_token: str | None = None
    _refresh_token: str | None = None
    _expires_at: dt.datetime | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def from_env(
        cls,
        assertion_provider: AssertionProvider,
        *,
        controlplane_url: str | None = None,
        org_id: str | None = None,
        idp_issuer: str | None = None,
        audience: str | None = None,
        requested_ttl_minutes: int | None = None,
    ) -> WorkforceTokenProvider:
        cp_url = (
            controlplane_url
            or os.getenv("SENTINOS_CONTROLPLANE_URL")
            or os.getenv("SENTINOS_APP_URL")
            or os.getenv("SENTINOS_CONSOLE_URL")
            or ""
        ).strip()
        org = (org_id or os.getenv("SENTINOS_ORG_ID") or "").strip()
        issuer = (
            idp_issuer
            or os.getenv("SENTINOS_WORKFORCE_IDP_ISSUER")
            # Backward-compatible alias (historical naming).
            or os.getenv("SENTINOS_WORKFORCE_AUTH_MODE")
            or ""
        ).strip()
        aud = (audience or os.getenv("SENTINOS_WORKFORCE_EXCHANGE_AUDIENCE") or "").strip() or None
        if requested_ttl_minutes is None:
            ttl_raw = (os.getenv("SENTINOS_WORKFORCE_REQUESTED_TTL_MINUTES") or "").strip()
            if ttl_raw:
                try:
                    requested_ttl_minutes = int(ttl_raw)
                except ValueError:
                    requested_ttl_minutes = None
        if not cp_url:
            raise WorkforceTokenError(
                "controlplane_url is required for workforce auth (set SENTINOS_CONTROLPLANE_URL or SENTINOS_APP_URL)"
            )
        if not org:
            raise WorkforceTokenError("SENTINOS_ORG_ID is required for workforce auth")
        if not issuer:
            raise WorkforceTokenError(
                "idp_issuer is required (set SENTINOS_WORKFORCE_IDP_ISSUER to your IdP issuer URL or pass idp_issuer)"
            )
        return cls(
            controlplane_url=cp_url,
            org_id=org,
            idp_issuer=issuer,
            audience=aud,
            requested_ttl_minutes=requested_ttl_minutes,
            assertion_provider=assertion_provider,
        )

    def __call__(self) -> str:
        return self.get_access_token()

    def get_access_token(self) -> str:
        with self._lock:
            # Two-pass flow:
            # 1) Use cached token when still fresh.
            # 2) If stale/expired, refresh when possible, else exchange.
            # This also handles an edge case where exchange returns an already-expired token.
            for _ in range(2):
                if self._is_token_fresh():
                    return self._access_token or ""

                if self._refresh_token:
                    try:
                        self._refresh()
                    except WorkforceSessionRevokedError:
                        self._exchange()
                    except WorkforceTokenError:
                        self._exchange()
                else:
                    self._exchange()

            if self._access_token:
                return self._access_token
            raise WorkforceTokenError("workforce token exchange did not return access_token")

    def _is_token_fresh(self) -> bool:
        if not self._access_token or not self._expires_at:
            return False
        now = dt.datetime.now(tz=dt.timezone.utc)
        refresh_cutoff = self._expires_at - dt.timedelta(seconds=max(0, self.refresh_skew_seconds))
        return now < refresh_cutoff

    def _exchange(self) -> None:
        assertion = self.assertion_provider()
        if not isinstance(assertion, WorkforceAssertion):
            raise WorkforceTokenError("assertion_provider must return WorkforceAssertion")
        if not assertion.external_subject.strip():
            raise WorkforceTokenError("assertion_provider returned empty external_subject")

        payload: dict[str, Any] = {
            "org_id": self.org_id,
            "idp_issuer": self.idp_issuer,
            "external_subject": assertion.external_subject,
        }
        if assertion.email:
            payload["email"] = assertion.email
        if assertion.display_name:
            payload["display_name"] = assertion.display_name
        if assertion.groups:
            payload["groups"] = assertion.groups
        if assertion.assertion_token:
            payload["assertion_token"] = assertion.assertion_token
        if assertion.token_binding_value:
            payload["token_binding_value"] = assertion.token_binding_value
        if assertion.device_id:
            payload["device_id"] = assertion.device_id
        if self.audience:
            payload["audience"] = self.audience
        if self.requested_ttl_minutes:
            payload["requested_ttl_minutes"] = int(self.requested_ttl_minutes)

        body = self._post_json("/v1/workforce/token/exchange", payload)
        tokens = body.get("tokens")
        if not isinstance(tokens, dict):
            raise WorkforceTokenError("exchange response missing tokens object")
        self._set_tokens(tokens)

    def _refresh(self) -> None:
        if not self._refresh_token:
            raise WorkforceTokenError("missing refresh token")
        body = self._post_json("/v1/workforce/token/refresh", {"refresh_token": self._refresh_token})
        self._set_tokens(body)

    def _set_tokens(self, payload: dict[str, Any]) -> None:
        access_token = str(payload.get("access_token") or "").strip()
        refresh_token = str(payload.get("refresh_token") or "").strip()
        expires_at_raw = str(payload.get("expires_at") or "").strip()
        if not access_token or not refresh_token or not expires_at_raw:
            raise WorkforceTokenError("token payload missing access_token, refresh_token, or expires_at")
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_at = _iso8601_utc(expires_at_raw)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = _normalize_base_url(self.controlplane_url) + path
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # noqa: PERF203
            detail = ""
            try:
                detail = exc.read().decode("utf-8")
            except Exception:
                detail = ""
            message = self._extract_error_message(detail) or f"HTTP {exc.code}"
            lower = message.lower()
            if exc.code in (401, 403):
                if "mapping" in lower or "group" in lower:
                    raise WorkforceMappingError(message) from exc
                raise WorkforcePolicyDeniedError(message) from exc
            if exc.code in (400, 404, 409):
                raise WorkforceTokenError(message) from exc
            if exc.code == 410 or "revoked" in lower or "expired" in lower:
                raise WorkforceSessionRevokedError(message) from exc
            raise WorkforceTokenError(message) from exc
        except urllib.error.URLError as exc:
            raise WorkforceTokenError(f"workforce token request failed: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WorkforceTokenError("workforce token endpoint returned non-JSON response") from exc
        if not isinstance(data, dict):
            raise WorkforceTokenError("workforce token endpoint returned invalid payload")
        return data

    @staticmethod
    def _extract_error_message(raw: str) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                msg = data.get("error")
                if isinstance(msg, str):
                    return msg.strip()
        except json.JSONDecodeError:
            pass
        return raw
