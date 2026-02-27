"""Async SDK usage example."""

import asyncio

from sentinos import SentinosClient


async def run_async_examples(client: SentinosClient) -> None:
    alerts = await client.alerts.list_alerts_async(limit=25)
    incidents = await client.incidents.list_incidents_async(limit=25)
    governance = await client.arbiter.governance_dashboard_async()
    print(len(alerts), len(incidents), governance.get("violations_24h"))


def main() -> None:
    client = SentinosClient.from_env(org_id="acme")
    asyncio.run(run_async_examples(client))


if __name__ == "__main__":
    main()
