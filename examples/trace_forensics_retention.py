"""Trace forensics, ledger verification, replay, and retention controls example."""

from __future__ import annotations

from sentinos import SentinosClient


def run_trace_forensics(client: SentinosClient, trace_id: str) -> None:
    signature = client.traces.verify_trace(trace_id)
    ledger = client.traces.ledger_verify(trace_id)
    replay = client.traces.replay_trace(
        trace_id,
        request={"include_explain": True},
    )
    distributed = client.traces.distributed_trace_summaries(limit=25)

    print("signature:", signature)
    print("ledger verified:", ledger.verified)
    print("drift detected:", replay.drift_detected)
    print("distributed traces:", len(distributed))


def run_retention_controls(client: SentinosClient) -> None:
    # Admin/SOC operations: inspect current policy and run dry-run enforcement.
    retention = client.traces.get_retention_policy()
    enforced = client.traces.enforce_retention(request={"dry_run": True})

    # Optional policy update flow. Keep existing values when you only want an auditable refresh.
    updated = client.traces.update_retention_policy(
        request={
            "trace_days": retention.trace_days,
            "export_days": retention.export_days,
            "ledger_days": retention.ledger_days,
        }
    )

    print("retention policy:", retention.to_dict())
    print("dry-run affected traces:", enforced.traces_affected)
    print("retention updated_at:", updated.updated_at.isoformat())

