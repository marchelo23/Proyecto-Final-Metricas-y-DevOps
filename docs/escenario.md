# Escenario provisional: ingesta y análisis de eventos (COM-01)

El enunciado detallado del escenario no está disponible. Esta matriz describe **sólo el MVP provisional acordado**; no atribuye estas reglas ni los roles `producer`/`analyst` a un enunciado oficial. La fuente de verdad provisional es el contrato coordinado COM-01–05. Si se recibe el escenario real, debe cotejarse antes de afirmar cobertura definitiva de #1.

| ID | Regla verificable del MVP | Prueba de aceptación (`tests/test_acceptance.py`) |
|---|---|---|
| MVP-01 | Ingesta autenticada devuelve 201, UUID, datos originales y fecha de ingestión UTC. | `test_ingestion_returns_persisted_event` |
| MVP-02 | Analista recupera el evento persistido; un UUID ausente produce 404 público. | `test_analyst_can_retrieve_event_and_missing_id_is_404` |
| MVP-03 | `(source, external_id)` es único: segundo intento devuelve 409 sin sustituir ni contar dos veces el evento; otra fuente puede reutilizar el `external_id`. | `test_duplicate_does_not_modify_or_duplicate_first_event`, `test_external_id_can_repeat_in_another_source` |
| MVP-04 | Agregados por `type` y `source`, ordenados por clave, total derivado; ventana vacía = cero. | `test_counts_by_type_and_source_are_sorted_and_empty_window_is_zero` |
| MVP-05 | Fechas timezone-aware en UTC; `[from, to)` incluye el inicio y excluye el fin, también al consultar con otro huso. | `test_counts_use_half_open_utc_window` |
| MVP-06 | Claves/roles provisionales: sólo `producer` ingresa, sólo `analyst` consulta; ausente = 401, rol incorrecto = 403. | `test_protected_routes_require_correct_role` |
| MVP-07 | La autorización se repite en el servicio incluso al llamarlo sin la ruta HTTP. | `test_service_rechecks_permission_before_repository_access` |
| MVP-08 | `from >= to` es entrada inválida (422 y error público). | `test_invalid_count_window_is_rejected` |
| MVP-09 | Identificadores y tamaños admitidos, carga útil objeto (máximo provisional 16 KiB), fechas con zona y `group_by` válido; entradas rechazadas con 422. | `test_ingestion_rejects_invalid_fields`, `test_counts_reject_invalid_query`; límite de carga útil: `tests/test_errors.py::test_payload_accepts_16_kib_and_rejects_one_byte_more` (COM-04) |
| MVP-10 | Liveness y readiness son públicas; con PostgreSQL disponible devuelven 200. | `test_health_endpoints_are_public` |

**Supuestos y límites:** identificadores simples, carga útil JSON objeto y campos obligatorios se validan en `schemas` (COM-04); las respuestas públicas de error son compartidas con COM-02/04. La restricción de unicidad y su resistencia a concurrencia corresponden al repositorio PostgreSQL (COM-03). No hay propiedad individual, eliminación, exportación, colas ni otros formatos en este MVP. Durabilidad ante reinicios, recuperación de DB y validaciones negativas exhaustivas se evidencian en las suites de COM-03/04, no se simulan aquí.

**Reproducción:** usar una base PostgreSQL **dedicada**, cuyo nombre contenga `test`, y nunca una de producción. Una vez levantado PostgreSQL 16 con una base vacía `events_test`:

```sh
export TEST_DATABASE_URL='postgresql+psycopg://usuario:clave@localhost:5432/events_test'
export DATABASE_URL="$TEST_DATABASE_URL"
export EVENT_PRODUCER_KEY='acceptance-producer-only'
export EVENT_ANALYST_KEY='acceptance-analyst-only'
uv run alembic upgrade head
mkdir -p artifacts
uv run pytest --junitxml=artifacts/junit.xml --html=artifacts/acceptance.html --self-contained-html
```

Las claves anteriores son valores descartables **sólo para pruebas**, no credenciales reales. `pytest-html` está en el grupo dev. Las pruebas HTTP usan `TestClient` contra la aplicación real; los eventos usan fuentes y ventanas temporales propias y sólo se eliminan las filas de esas fuentes. Si falta `TEST_DATABASE_URL`, se omiten las pruebas de integración; si está configurada y la DB no funciona, fallan. CI proporciona PostgreSQL 16, migra, ejecuta la suite y adjunta JUnit/HTML incluso cuando falla. Los archivos de CI constituyen el mecanismo de evidencia; no se afirma un resultado hasta ejecutarlo tras integrar las dependencias.
