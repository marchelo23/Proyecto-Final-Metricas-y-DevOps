"""PostgreSQL persistence adapter for events and derived counts."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    func,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings
from .contracts import DuplicateEvent, StorageUnavailable

metadata = MetaData()
events = Table(
    "events",
    metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True),
    Column("source", String(64), nullable=False),
    Column("external_id", String(128), nullable=False),
    Column("type", String(64), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSONB, nullable=False),
    UniqueConstraint("source", "external_id", name="uq_events_source_external_id"),
    Index("ix_events_occurred_at_type", "occurred_at", "type"),
)


@dataclass(frozen=True)
class StoredEvent:
    id: UUID
    source: str
    external_id: str
    type: str
    occurred_at: datetime
    ingested_at: datetime
    payload: dict


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    return value.astimezone(UTC)


def _stored_event(row: dict) -> StoredEvent:
    return StoredEvent(
        id=row["id"],
        source=row["source"],
        external_id=row["external_id"],
        type=row["type"],
        occurred_at=_utc(row["occurred_at"]),
        ingested_at=_utc(row["ingested_at"]),
        payload=row["payload"],
    )


class EventRepository:
    """Owns a supplied SQLAlchemy session; commits writes, rolls back DB errors."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _rollback(self) -> None:
        try:
            self._session.rollback()
        except SQLAlchemyError as exc:
            raise StorageUnavailable("Event storage unavailable") from exc

    def create(
        self,
        *,
        source: str,
        external_id: str,
        event_type: str,
        occurred_at: datetime,
        payload: dict,
    ) -> StoredEvent:
        occurred_at = _utc(occurred_at)
        try:
            row = (
                self._session.execute(
                    insert(events)
                    .values(
                        id=uuid4(),
                        source=source,
                        external_id=external_id,
                        type=event_type,
                        occurred_at=occurred_at,
                        ingested_at=datetime.now(UTC),
                        payload=payload,
                    )
                    .returning(*events.c)
                )
                .mappings()
                .one()
            )
            stored = _stored_event(row)
            self._session.commit()
            return stored
        except IntegrityError as exc:
            self._rollback()
            if (
                getattr(exc.orig, "sqlstate", None) == "23505"
                and getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                == "uq_events_source_external_id"
            ):
                raise DuplicateEvent("Event already exists") from exc
            raise StorageUnavailable("Event storage unavailable") from exc
        except SQLAlchemyError as exc:
            self._rollback()
            raise StorageUnavailable("Event storage unavailable") from exc

    def get(self, event_id: UUID) -> StoredEvent | None:
        try:
            row = (
                self._session.execute(select(events).where(events.c.id == event_id))
                .mappings()
                .one_or_none()
            )
            return _stored_event(row) if row is not None else None
        except SQLAlchemyError as exc:
            self._rollback()
            raise StorageUnavailable("Event storage unavailable") from exc

    def counts(
        self, *, start: datetime, end: datetime, group_by: Literal["type", "source"]
    ) -> list[tuple[str, int]]:
        if group_by not in ("type", "source"):
            raise ValueError("group_by must be 'type' or 'source'")
        start, end = _utc(start), _utc(end)
        grouping = events.c[group_by]
        try:
            rows = self._session.execute(
                select(grouping, func.count())
                .where(events.c.occurred_at >= start, events.c.occurred_at < end)
                .group_by(grouping)
                .order_by(grouping)
            ).all()
            return [(key, count) for key, count in rows]
        except SQLAlchemyError as exc:
            self._rollback()
            raise StorageUnavailable("Event storage unavailable") from exc


@lru_cache(maxsize=8)
def _session_factory(database_url: str) -> sessionmaker[Session]:
    # Cache per URL: pre_ping replaces stale pooled connections after a DB restart.
    engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine)


def get_repository() -> Iterator[EventRepository]:
    """FastAPI dependency: one session per request, configured from DATABASE_URL."""
    try:
        factory = _session_factory(Settings.from_env().database_url)
    except SQLAlchemyError as exc:
        raise StorageUnavailable("Event storage unavailable") from exc
    with factory() as session:
        yield EventRepository(session)
