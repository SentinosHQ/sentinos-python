from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError

import pytest

from sentinos.auth.workforce import (
    WorkforceAssertion,
    WorkforcePolicyDeniedError,
    WorkforceTokenProvider,
)


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> _FakeHTTPResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeHTTPErrorBody:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        return None


def test_workforce_provider_exchanges_and_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_urlopen(req, timeout=10.0):
        body = json.loads(req.data.decode("utf-8"))
        calls.append((req.full_url, body))
        return _FakeHTTPResponse(
            {
                "tokens": {
                    "access_token": "access-1",
                    "refresh_token": "refresh-1",
                    "expires_at": "2099-01-01T00:00:00Z",
                    "refresh_expires_at": "2099-01-02T00:00:00Z",
                    "session_id": "sess-1",
                    "org_id": "org-1",
                    "tenant_id": "org-1",
                    "membership_id": "m-1",
                    "permissions": ["traces.read"],
                    "roles": ["standard"],
                },
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = WorkforceTokenProvider(
        controlplane_url="https://controlplane.example",
        org_id="org-1",
        idp_issuer="https://idp.example.com",
        assertion_provider=lambda: WorkforceAssertion(
            external_subject="subject-123",
            email="worker@example.com",
            display_name="Worker",
            groups=["AI_USERS"],
        ),
    )

    first = provider.get_access_token()
    second = provider.get_access_token()

    assert first == "access-1"
    assert second == "access-1"
    assert len(calls) == 1
    assert calls[0][0].endswith("/v1/workforce/token/exchange")
    assert calls[0][1]["org_id"] == "org-1"
    assert calls[0][1]["idp_issuer"] == "https://idp.example.com"


def test_workforce_provider_refreshes_token(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_urlopen(req, timeout=10.0):
        calls.append(req.full_url)
        body = json.loads(req.data.decode("utf-8"))
        if req.full_url.endswith("/v1/workforce/token/exchange"):
            return _FakeHTTPResponse(
                {
                    "tokens": {
                        "access_token": "access-old",
                        "refresh_token": "refresh-old",
                        "expires_at": "2000-01-01T00:00:00Z",
                        "refresh_expires_at": "2099-01-02T00:00:00Z",
                        "session_id": "sess-1",
                        "org_id": "org-1",
                        "tenant_id": "org-1",
                        "membership_id": "m-1",
                        "permissions": ["traces.read"],
                        "roles": ["standard"],
                    },
                }
            )
        assert body["refresh_token"] == "refresh-old"
        return _FakeHTTPResponse(
            {
                "access_token": "access-new",
                "refresh_token": "refresh-new",
                "expires_at": "2099-01-01T00:00:00Z",
                "refresh_expires_at": "2099-01-02T00:00:00Z",
                "session_id": "sess-1",
                "org_id": "org-1",
                "tenant_id": "org-1",
                "membership_id": "m-1",
                "permissions": ["traces.read"],
                "roles": ["standard"],
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = WorkforceTokenProvider(
        controlplane_url="https://controlplane.example",
        org_id="org-1",
        idp_issuer="https://idp.example.com",
        assertion_provider=lambda: WorkforceAssertion(external_subject="subject-123"),
    )

    token = provider.get_access_token()
    assert token == "access-new"
    assert calls[0].endswith("/v1/workforce/token/exchange")
    assert calls[1].endswith("/v1/workforce/token/refresh")


def test_workforce_provider_maps_policy_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=10.0):
        payload = json.dumps({"error": "workforce policy is disabled for organization"}).encode("utf-8")
        raise HTTPError(req.full_url, 403, "forbidden", hdrs=None, fp=_FakeHTTPErrorBody(payload))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = WorkforceTokenProvider(
        controlplane_url="https://controlplane.example",
        org_id="org-1",
        idp_issuer="https://idp.example.com",
        assertion_provider=lambda: WorkforceAssertion(external_subject="subject-123"),
    )

    with pytest.raises(WorkforcePolicyDeniedError):
        _ = provider.get_access_token()


def test_workforce_provider_session_revoked_falls_back_to_exchange(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_urlopen(req, timeout=10.0):
        calls.append(req.full_url)
        if req.full_url.endswith("/v1/workforce/token/exchange"):
            exchange_count = calls.count("https://controlplane.example/v1/workforce/token/exchange")
            expires_at = "2000-01-01T00:00:00Z" if exchange_count == 1 else "2099-01-01T00:00:00Z"
            access_token = "access-start" if exchange_count == 1 else "access-fallback"
            return _FakeHTTPResponse(
                {
                    "tokens": {
                        "access_token": access_token,
                        "refresh_token": "refresh-start",
                        "expires_at": expires_at,
                        "refresh_expires_at": "2099-01-02T00:00:00Z",
                        "session_id": "sess-1",
                        "org_id": "org-1",
                        "tenant_id": "org-1",
                        "membership_id": "m-1",
                        "permissions": ["traces.read"],
                        "roles": ["standard"],
                    },
                }
            )
        if req.full_url.endswith("/v1/workforce/token/refresh"):
            payload = json.dumps({"error": "workforce session expired"}).encode("utf-8")
            raise HTTPError(req.full_url, 410, "gone", hdrs=None, fp=_FakeHTTPErrorBody(payload))
        raise AssertionError("unexpected URL")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = WorkforceTokenProvider(
        controlplane_url="https://controlplane.example",
        org_id="org-1",
        idp_issuer="https://idp.example.com",
        assertion_provider=lambda: WorkforceAssertion(external_subject="subject-123"),
    )

    token = provider.get_access_token()
    assert token == "access-fallback"
    assert calls.count("https://controlplane.example/v1/workforce/token/exchange") == 2
