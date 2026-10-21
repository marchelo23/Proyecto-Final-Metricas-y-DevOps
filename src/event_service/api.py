"""HTTP routes for ingestion, retrieval and on-demand event counts."""

from datetime import timezone
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from .auth import Principal, require_analyst, require_producer
from .schemas import CountsQuery, EventCreate
from .service import count_events, create_event, get_event
from .storage import EventRepository, StoredEvent, get_repository

router = APIRouter(prefix="/v1")


def _event_document(event: StoredEvent) -> dict[str, Any]:
    """Only expose fields in the public contract, never ORM internals."""
    return {
        "id": event.id,
        "source": event.source,
        "external_id": event.external_id,
        "type": event.type,
        "occurred_at": event.occurred_at.astimezone(timezone.utc),
        "payload": event.payload,
        "ingested_at": event.ingested_at.astimezone(timezone.utc),
    }


@router.post("/events", status_code=201)
def post_event(
    event: EventCreate,
    principal: Annotated[Principal, Depends(require_producer)],
    repository: Annotated[EventRepository, Depends(get_repository)],
) -> dict[str, Any]:
    return _event_document(create_event(event, principal, repository))


@router.get("/events/{event_id}")
def read_event(
    event_id: UUID,
    principal: Annotated[Principal, Depends(require_analyst)],
    repository: Annotated[EventRepository, Depends(get_repository)],
) -> dict[str, Any]:
    return _event_document(get_event(event_id, principal, repository))


@router.get("/analysis/counts")
def read_counts(
    query: Annotated[CountsQuery, Query()],
    principal: Annotated[Principal, Depends(require_analyst)],
    repository: Annotated[EventRepository, Depends(get_repository)],
) -> dict[str, object]:
    return count_events(query, principal, repository)
