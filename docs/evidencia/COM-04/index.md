# COM-04 — Evidencia local de validación y recuperación (MVP)

**Criterios:** entradas inválidas reciben 422, duplicados 409, ausencias 404, dependencia caída 503 y recuperación sin reiniciar la aplicación. Respuestas y logs llevan `request_id` sin secretos; véanse [issue #4](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/4) y [matriz/procedimiento](../../arquitectura/errores.md).

## Pruebas automatizadas

Con `TEST_DATABASE_URL` apuntando exclusivamente a PostgreSQL de pruebas y migración aplicada:

```bash
uv sync --locked
uv run --locked pytest -q
```

**Esperado:** esquema, manejo público de errores, no filtración de datos y base funcional. **Obtenido (2026-10-21, rama COM-04 apilada):** `64 passed` (COM-02/03/04), 7 advertencias de dependencias; Postgres real para pruebas COM-03. `GET /health/ready` comparte ahora el manejador de `StorageUnavailable`, por lo que `error.request_id` coincide con la cabecera.

## Caída y recuperación reales

El procedimiento reproducible está en `docs/arquitectura/errores.md`: arrancar API **una vez**, consultar agregados, detener **el contenedor PostgreSQL de pruebas** sin borrar volumen, consultar otra vez, restaurar el mismo contenedor y consultar de nuevo. **Obtenido en rama integrada (2026-10-21):**

```text
status=200 request_id=before-1 code=OK
status=503 request_id=down-1 code=DEPENDENCY_UNAVAILABLE
status=200 request_id=after-1 code=OK
PASS: PostgreSQL recovered without restarting API
```

El experimento utilizó el mismo PID de API durante las tres peticiones y un PostgreSQL 16 local de pruebas. **La consulta funcional requiere COM-01**, ausente en este PR aislado; no afirmar que el experimento es ejecutable antes de integrar ese PR.

## Pendiente

Workflow run, revisión ajena, despliegue en defensa, correlación completa con logs/trazas de MET-02/04 y enlace de evidencia desde el issue. No cerrar #4 solo con la evidencia local.
