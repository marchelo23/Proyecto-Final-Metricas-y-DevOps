"""Business operations for the provisional event-ingestion MVP."""

from datetime import UTC
from uuid import UUID

from .auth import Principal, ensure_permission
from .contracts import EventNotFound
from .schemas import CountsQuery, EventCreate
from .storage import EventRepository, StoredEvent


def create_event(
    event: EventCreate, principal: Principal, repository: EventRepository
) -> StoredEvent:
    """Persist an event; the repository enforces (source, external_id) uniqueness."""
    ensure_permission(principal, "events:create")
    return repository.create(
        source=event.source,
        external_id=event.external_id,
        event_type=event.type,
        occurred_at=event.occurred_at.astimezone(UTC),
        payload=event.payload,
    )


def get_event(
    event_id: UUID, principal: Principal, repository: EventRepository
) -> StoredEvent:
    ensure_permission(principal, "events:read")
    event = repository.get(event_id)
    if event is None:
        raise EventNotFound(event_id)
    return event


def count_events(
    query: CountsQuery, principal: Principal, repository: EventRepository
) -> dict[str, object]:
    ensure_permission(principal, "analysis:read")
    # Use the wire aliases rather than assuming the Python name for `from`.
    window = query.model_dump(by_alias=True)
    start = window["from"].astimezone(UTC)
    end = window["to"].astimezone(UTC)
    group_by = window["group_by"]
    buckets = sorted(
        repository.counts(start=start, end=end, group_by=group_by),
        key=lambda item: item[0],
    )
    return {
        "total": sum(count for _, count in buckets),
        "group_by": group_by,
        "window": {"from": start, "to": end},
        "buckets": [{"key": key, "count": count} for key, count in buckets],
    }
