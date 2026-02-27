"""SSE event stream example."""

from sentinos import SentinosClient


def consume_events(client: SentinosClient, *, last_event_id: str | None = None) -> None:
    for line in client.kernel.events_stream(last_event_id=last_event_id, timeout_seconds=30):
        print(line)
