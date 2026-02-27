from __future__ import annotations

from sentinos.client import SentinosClient


def test_sentinos_client_base_url_fans_out_to_all_services() -> None:
    client = SentinosClient(base_url="https://api.sentinos.ai")

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.kernel_url == "https://api.sentinos.ai"
    assert client.config.arbiter_url == "https://api.sentinos.ai"
    assert client.config.chronos_url == "https://api.sentinos.ai"
    assert client.config.controlplane_url == "https://api.sentinos.ai"


def test_sentinos_client_service_url_overrides_base_url() -> None:
    client = SentinosClient(
        base_url="https://api.sentinos.ai",
        kernel_url="https://kernel.sentinos.ai",
        arbiter_url="https://arbiter.sentinos.ai/",
        controlplane_url="https://controlplane.sentinos.ai/",
    )

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.kernel_url == "https://kernel.sentinos.ai"
    assert client.config.arbiter_url == "https://arbiter.sentinos.ai"
    assert client.config.chronos_url == "https://api.sentinos.ai"
    assert client.config.controlplane_url == "https://controlplane.sentinos.ai"


def test_sentinos_client_default_localhost_urls_when_base_not_set() -> None:
    client = SentinosClient()

    assert client.config.base_url is None
    assert client.config.kernel_url == "http://localhost:8081"
    assert client.config.arbiter_url == "http://localhost:8082"
    assert client.config.chronos_url == "http://localhost:8083"
    assert client.config.controlplane_url == "http://localhost:18084"


def test_sentinos_client_local_base_url_does_not_override_controlplane_default() -> None:
    client = SentinosClient(base_url="http://localhost:8081")

    assert client.config.kernel_url == "http://localhost:8081"
    assert client.config.arbiter_url == "http://localhost:8081"
    assert client.config.chronos_url == "http://localhost:8081"
    assert client.config.controlplane_url == "http://localhost:18084"


def test_sentinos_client_api_url_alias_fans_out() -> None:
    client = SentinosClient(api_url="https://api.sentinos.ai/")

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.kernel_url == "https://api.sentinos.ai"
    assert client.config.arbiter_url == "https://api.sentinos.ai"
    assert client.config.chronos_url == "https://api.sentinos.ai"
    assert client.config.controlplane_url == "https://api.sentinos.ai"


def test_sentinos_client_url_alias_fans_out() -> None:
    client = SentinosClient(url="https://api.sentinos.ai/")

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.kernel_url == "https://api.sentinos.ai"
    assert client.config.arbiter_url == "https://api.sentinos.ai"
    assert client.config.chronos_url == "https://api.sentinos.ai"
    assert client.config.controlplane_url == "https://api.sentinos.ai"


def test_sentinos_client_base_url_precedence_over_aliases() -> None:
    client = SentinosClient(
        url="https://url.sentinos.ai",
        api_url="https://api.sentinos.ai",
        base_url="https://base.sentinos.ai",
    )

    assert client.config.base_url == "https://base.sentinos.ai"
    assert client.config.kernel_url == "https://base.sentinos.ai"
    assert client.config.arbiter_url == "https://base.sentinos.ai"
    assert client.config.chronos_url == "https://base.sentinos.ai"
    assert client.config.controlplane_url == "https://base.sentinos.ai"


def test_sentinos_client_simple_helper() -> None:
    client = SentinosClient.simple(
        base_url="https://api.sentinos.ai/",
        tenant_id="org-1",
        auth_token="token-1",
    )

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.tenant_id == "org-1"
    assert client.config.kernel_url == "https://api.sentinos.ai"
    assert client.config.controlplane_url == "https://api.sentinos.ai"


def test_sentinos_client_org_id_alias_sets_tenant_id() -> None:
    client = SentinosClient(base_url="https://api.sentinos.ai", org_id="org-2")
    assert client.config.tenant_id == "org-2"


def test_sentinos_client_org_id_alias_conflict_raises() -> None:
    try:
        SentinosClient(base_url="https://api.sentinos.ai", tenant_id="org-a", org_id="org-b")
    except ValueError as e:
        assert "tenant_id and org_id must match" in str(e)
    else:
        raise AssertionError("expected ValueError on tenant_id/org_id mismatch")


def test_sentinos_client_from_env_base_url(monkeypatch) -> None:
    monkeypatch.setenv("SENTINOS_BASE_URL", "https://api.sentinos.ai/")
    monkeypatch.setenv("SENTINOS_TENANT_ID", "tenant-a")
    monkeypatch.setenv("SENTINOS_ACCESS_TOKEN", "token-a")

    client = SentinosClient.from_env()

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.tenant_id == "tenant-a"
    assert client.config.kernel_url == "https://api.sentinos.ai"
    assert client.config.arbiter_url == "https://api.sentinos.ai"
    assert client.config.chronos_url == "https://api.sentinos.ai"
    assert client.config.controlplane_url == "https://api.sentinos.ai"


def test_sentinos_client_from_env_respects_service_overrides(monkeypatch) -> None:
    monkeypatch.setenv("SENTINOS_API_URL", "https://api.sentinos.ai")
    monkeypatch.setenv("SENTINOS_KERNEL_URL", "https://kernel.internal")
    monkeypatch.setenv("SENTINOS_ARBITER_URL", "https://arbiter.internal/")
    monkeypatch.setenv("SENTINOS_CHRONOS_URL", "https://chronos.internal")
    monkeypatch.setenv("SENTINOS_CONTROLPLANE_URL", "https://controlplane.internal/")
    monkeypatch.setenv("SENTINOS_ORG_ID", "org-via-alias")
    monkeypatch.setenv("SENTINOS_TIMEOUT_SECONDS", "45")

    client = SentinosClient.from_env()

    assert client.config.base_url == "https://api.sentinos.ai"
    assert client.config.kernel_url == "https://kernel.internal"
    assert client.config.arbiter_url == "https://arbiter.internal"
    assert client.config.chronos_url == "https://chronos.internal"
    assert client.config.controlplane_url == "https://controlplane.internal"
    assert client.config.tenant_id == "org-via-alias"
    assert client.config.timeout_seconds == 45.0


def test_sentinos_client_from_env_org_id_param_alias_sets_tenant_id(monkeypatch) -> None:
    monkeypatch.delenv("SENTINOS_TENANT_ID", raising=False)
    monkeypatch.delenv("SENTINOS_ORG_ID", raising=False)

    client = SentinosClient.from_env(org_id="org-param")
    assert client.config.tenant_id == "org-param"


def test_sentinos_client_from_env_org_id_conflict_raises() -> None:
    try:
        SentinosClient.from_env(tenant_id="org-a", org_id="org-b")
    except ValueError as e:
        assert "tenant_id and org_id must match" in str(e)
    else:
        raise AssertionError("expected ValueError on tenant_id/org_id mismatch")
