# COM-03 — Evidencia local de persistencia (MVP)

**Criterio:** los eventos sobreviven el reinicio de la aplicación y de PostgreSQL; las migraciones son versionadas y una segunda ejecución no borra datos. Véanse [issue #3](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/3), [procedimiento y límites](../../arquitectura/persistencia.md) y `scripts/verify_durability.py`.

## Reproducir

En una base PostgreSQL **dedicada a pruebas** (`*_test`) y con `DATABASE_URL=TEST_DATABASE_URL`:

```bash
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked pytest -q tests/test_skeleton.py tests/test_persistence.py
```

**Esperado:** crear y leer datos, respetar unicidad aun con inserciones concurrentes, consultar agregados y reaplicar migraciones sin pérdida. **Obtenido (2026-10-21):** `15 passed` (8 de base + 7 de persistencia), con PostgreSQL 16 real en Compose y volumen nombrado; 7 advertencias de dependencias/Alembic. No se utilizó base de producción.

Con COM-01 integrado, ejecutar el experimento completo `uv run --locked python scripts/verify_durability.py`: escribe por API, detiene API, detiene y arranca **el mismo** contenedor PostgreSQL con su volumen, vuelve a migrar, arranca API y lee por el mismo ID. **Obtenido en rama de integración (2026-10-21):** `PASS: event a8e98163-4488-4e3f-afc1-a6a181b81163 persisted after API + PostgreSQL restart`. La prueba completa depende de la ruta HTTP del PR COM-01; no se afirma ejecutable en este PR aislado.

## Límites y pendientes

- Se demuestra reinicio de procesos/pods con volumen conservado; **no** recuperación ante pérdida total de la VM. La política de respaldo depende de reglas del escenario no recibidas.
- Pendientes workflow run, despliegue K3s, enlace del PR desde el issue, revisión por otra persona y demostración en defensa. No cerrar #3 con la evidencia local sola.
