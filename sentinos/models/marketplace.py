from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .policy import PolicyMetadata


class MarketplacePolicySpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    policy_id: str
    rego: str
    metadata: PolicyMetadata


class MarketplacePack(BaseModel):
    model_config = ConfigDict(extra="allow")

    pack_id: str
    tenant_id: str | None = None
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    verified: bool = False
    policies: list[MarketplacePolicySpec] = []
    tags: list[str] = []
    install_count: int = 0
    created_at: datetime


class PackInstall(BaseModel):
    model_config = ConfigDict(extra="allow")

    install_id: str
    tenant_id: str
    pack_id: str
    installed_version: str
    status: str
    simulation_job_ids: list[str] = []
    installed_at: datetime | None = None
    installed_by: str | None = None


class InstallResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    install_id: str
    simulation_job_ids: list[str] = []
    raw: dict[str, Any] = {}

