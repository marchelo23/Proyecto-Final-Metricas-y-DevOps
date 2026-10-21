"""Alembic environment; never create tables outside versioned migrations."""

from event_service.config import Settings
from sqlalchemy import create_engine, pool

from alembic import context
from event_service.storage import metadata


def run_migrations_offline() -> None:
    context.configure(
        url=Settings.from_env().database_url,
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        Settings.from_env().database_url,
        poolclass=pool.NullPool,
        pool_pre_ping=True,
    )
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
