from __future__ import annotations

from inspect import isawaitable
from typing import Any

from sentinos_core import AuthenticatedClient, Client

CoreClient = Client | AuthenticatedClient


def require_tenant(default_tenant: str | None, tenant_id: str | None, *, field_name: str = "tenant_id") -> str:
    value = (tenant_id or default_tenant or "").strip()
    if not value:
        raise ValueError(f"{field_name} is required (set it on SentinosClient or pass it per call)")
    return value


def core_with_headers(
    core: CoreClient,
    *,
    tenant_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> CoreClient:
    headers: dict[str, str] = {}
    if tenant_id:
        headers["x-tenant-id"] = tenant_id
    if extra_headers:
        headers.update(extra_headers)
    return core.with_headers(headers) if headers else core


def _sync_dispatch(http: Any, method: str, path: str, *, params: dict[str, Any] | None, body: Any) -> Any:
    func = getattr(http, method.lower(), None)
    if func is not None:
        kwargs: dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if body is not None:
            kwargs["json"] = body
        return func(path, **kwargs)
    request_kwargs: dict[str, Any] = {"method": method.upper(), "url": path}
    if params:
        request_kwargs["params"] = params
    if body is not None:
        request_kwargs["json"] = body
    return http.request(**request_kwargs)


async def _async_dispatch(http: Any, method: str, path: str, *, params: dict[str, Any] | None, body: Any) -> Any:
    func = getattr(http, method.lower(), None)
    if func is not None:
        kwargs: dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if body is not None:
            kwargs["json"] = body
        result = await func(path, **kwargs)
        while isawaitable(result):
            result = await result
        return result
    request_kwargs: dict[str, Any] = {"method": method.upper(), "url": path}
    if params:
        request_kwargs["params"] = params
    if body is not None:
        request_kwargs["json"] = body
    result = await http.request(**request_kwargs)
    while isawaitable(result):
        result = await result
    return result


def request_json(
    core: CoreClient,
    method: str,
    path: str,
    *,
    tenant_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    body: Any = None,
) -> dict[str, Any]:
    scoped = core_with_headers(core, tenant_id=tenant_id, extra_headers=extra_headers)
    response = _sync_dispatch(scoped.get_httpx_client(), method, path, params=params, body=body)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        return data
    return {"data": data}


async def request_json_async(
    core: CoreClient,
    method: str,
    path: str,
    *,
    tenant_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    body: Any = None,
) -> dict[str, Any]:
    scoped = core_with_headers(core, tenant_id=tenant_id, extra_headers=extra_headers)
    response = await _async_dispatch(scoped.get_async_httpx_client(), method, path, params=params, body=body)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        return data
    return {"data": data}
