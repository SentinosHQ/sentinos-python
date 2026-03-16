"""Native gRPC execute example for Sentinos KernelProtocol."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Sequence

try:
    import grpc
    from google.protobuf import json_format
    from google.protobuf.struct_pb2 import Struct
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    missing = str(exc)
    print(
        f"Missing dependency for gRPC smoke test ({missing}). "
        "Install with: pip install 'sentinos[grpc]'",
        file=sys.stderr,
    )
    raise


KERNEL_GRPC_METHOD = "/sentinos.kernel.v1.KernelProtocol/Execute"


def _parse_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_channel(target: str) -> grpc.Channel:
    use_tls = _parse_bool_env("SENTINOS_GRPC_TLS", False)
    if not use_tls:
        return grpc.insecure_channel(target)

    ca_file = os.getenv("SENTINOS_GRPC_CA_FILE")
    cert_file = os.getenv("SENTINOS_GRPC_CERT_FILE")
    key_file = os.getenv("SENTINOS_GRPC_KEY_FILE")

    root_certs = open(ca_file, "rb").read() if ca_file else None
    private_key = open(key_file, "rb").read() if key_file else None
    cert_chain = open(cert_file, "rb").read() if cert_file else None
    creds = grpc.ssl_channel_credentials(
        root_certificates=root_certs,
        private_key=private_key,
        certificate_chain=cert_chain,
    )
    return grpc.secure_channel(target, creds)


def _metadata() -> Sequence[tuple[str, str]]:
    md: list[tuple[str, str]] = []
    token = os.getenv("SENTINOS_ACCESS_TOKEN", "").strip()
    if token:
        md.append(("authorization", f"Bearer {token}"))
    api_key = os.getenv("SENTINOS_API_KEY", "").strip()
    if api_key:
        md.append(("x-api-key", api_key))
    return md


def main() -> None:
    target = os.getenv("SENTINOS_GRPC_TARGET", "").strip()
    if not target:
        raise SystemExit("Set SENTINOS_GRPC_TARGET to your Sentinos Kernel gRPC endpoint before running this example.")
    tenant_id = (os.getenv("SENTINOS_ORG_ID") or os.getenv("SENTINOS_TENANT_ID") or "acme").strip()
    agent_id = os.getenv("SENTINOS_GRPC_AGENT_ID", "grpc-smoke-agent")
    session_id = os.getenv("SENTINOS_GRPC_SESSION_ID", "grpc-smoke-session")
    tool_name = os.getenv("SENTINOS_GRPC_TOOL", "stripe.refund")

    payload = Struct()
    payload.update(
        {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "intent": {
                "type": "tool_call",
                "tool": tool_name,
                "args": {"amount": 25, "currency": "USD"},
            },
        }
    )

    channel = _load_channel(target)
    stub = channel.unary_unary(
        KERNEL_GRPC_METHOD,
        request_serializer=Struct.SerializeToString,
        response_deserializer=Struct.FromString,
    )
    response = stub(payload, metadata=_metadata(), timeout=20)
    response_map = json_format.MessageToDict(response, preserving_proto_field_name=True)
    print(json.dumps(response_map, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
