# COM-03 — Persistencia del MVP de eventos

`EventRepository` (`src/event_service/storage.py`) es el adaptador PostgreSQL de la
aplicación. Recibe una `sqlalchemy.orm.Session`; `get_repository()` es la
dependencia FastAPI que crea/cierra una sesión por solicitud usando
`Settings.from_env().database_url`. El engine se reutiliza por URL con
`pool_pre_ping=True`: si PostgreSQL reinicia, una conexión caducada se
descarta antes de reutilizarla, sin reiniciar el proceso API. No hay reintento
automático de escritura: una operación durante la caída devuelve
`StorageUnavailable` y se puede repetir desde el cliente después de recuperar
la base. La sesión hace rollback al fallar una operación de DB.

La tabla `events` tiene UUID, `source`, `external_id`, `type`, dos `timestamptz`
(`occurred_at`, `ingested_at`) y `payload` JSONB. `occurred_at` se normaliza a
UTC; el repositorio genera ID e `ingested_at` UTC. La unicidad
`(source,external_id)` la garantiza PostgreSQL (`uq_events_source_external_id`),
incluso para inserciones concurrentes: el error `23505` de esa restricción se
convierte en `DuplicateEvent` y no altera el evento previo. El índice
`ix_events_occurred_at_type` ayuda al rango temporal y al agrupamiento por
tipo. `counts` deriva agregados de eventos en `[start,end)`, ordenados por
clave; no persiste contadores independientes. Las respuestas de errores son
responsabilidad de COM-04 y no deben exponer la excepción SQL encadenada.

## Inicialización local

Prerequisitos: PostgreSQL 16 por `docker compose` (en el entorno de defensa
`docker` es un wrapper de Podman), Python 3.13, `uv` y las dependencias de
COM-02. Ejemplo de variables **solo en la terminal**, sin valores reales en
Git; escapar con URL encoding los caracteres especiales de la contraseña en
`DATABASE_URL`:

```sh
export POSTGRES_PASSWORD='<contraseña-local>'
export POSTGRES_DB=events_test
export POSTGRES_PORT=15433
export DATABASE_URL='postgresql+psycopg://events:<contraseña-URL-encoded>@127.0.0.1:15433/events_test'
export TEST_DATABASE_URL="$DATABASE_URL"
docker compose -p com03-defensa up -d postgres
uv run alembic upgrade head
uv run pytest tests/test_persistence.py
docker compose -p com03-defensa stop postgres
```

Compose publica solo en `127.0.0.1`, exige `POSTGRES_PASSWORD`, y utiliza un
volumen nombrado (`<proyecto>_postgres_data`). No usar `down -v`: elimina los
datos. `alembic upgrade head` crea el esquema versionado; ejecutarlo de nuevo
no aplica DDL por segunda vez gracias a `alembic_version`. La aplicación **no**
llama `create_all`. El downgrade de la primera versión borra la tabla:
**no ejecutarlo sobre datos que se quieran conservar**.

Las pruebas requieren `TEST_DATABASE_URL` separado y con nombre `test_*` o
`*_test`; no borran base ni tablas, solo registros que ellas mismas crean.
Cubren inserción/lectura, ventana semiabierta, duplicado concurrente,
reutilización en un engine nuevo y migración repetida. Sin la base de COM-02
(`config.py`, `contracts.py`, `pyproject.toml`) todavía no pueden ejecutarse
standalone.

## Defensa: reinicio real conservando volumen

Con `POSTGRES_PASSWORD`, `DATABASE_URL` apuntando a la base de test local y
`EVENT_PRODUCER_KEY`/`EVENT_ANALYST_KEY` definidos, ejecutar:

```sh
uv run python scripts/verify_durability.py
```

El script usa su propio proyecto Compose (`com03-defense-<uid>` por defecto)
y puerto `15433`, migra, arranca la API, crea un evento, **detiene la API y
PostgreSQL**, arranca el mismo almacenamiento, reaplica la migración dos veces,
arranca un proceso API nuevo y consulta/valida el evento por ID. Detiene ambos
procesos al terminar pero **conserva el volumen**. Ajustar `COMPOSE_PROJECT_NAME`,
`POSTGRES_PORT`, `API_PORT` y `DATABASE_URL` juntos si hay colisiones. El script
se niega a usar una URL que no sea local ni una DB cuyo nombre no sea de test.

Límites: volumen local no garantiza supervivencia a destrucción de la VM ni
alta disponibilidad; la comprobación automatizada solo es válida con Compose,
el esqueleto HTTP y credenciales de prueba integrados. El test de recuperación
sin reiniciar la API frente a indisponibilidad temporal es propiedad de COM-04.
