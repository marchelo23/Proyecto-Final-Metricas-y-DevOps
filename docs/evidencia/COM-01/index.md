# COM-01 — Evidencia local del MVP de eventos

**Criterio:** las funciones y reglas definidas para el [MVP inicial de ingesta y análisis de eventos](../../escenario.md) tienen pruebas de aceptación trazables. El alcance recibido es el tema y los requisitos COM; la matriz explicita las decisiones adoptadas para concretarlo. Véase [issue #1](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/1).

## Reproducir desde una base PostgreSQL de pruebas

Con `TEST_DATABASE_URL=DATABASE_URL` apuntando exclusivamente a una base `*_test`, claves de prueba en `EVENT_PRODUCER_KEY`/`EVENT_ANALYST_KEY` y PostgreSQL 16 en marcha:

```bash
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked pytest --junitxml=/tmp/opencode/com01-junit.xml --html=/tmp/opencode/com01-report.html --self-contained-html
```

**Esperado:** ingesta, consulta, agregación por tiempo/tipo/fuente, unicidad, validaciones y autorización pasan; la suite falla si falla un caso. **Obtenido (2026-10-21, rama integrada):** `121 passed, 7 warnings`; 23 casos en `tests/test_acceptance.py` ejecutados contra la API real con PostgreSQL. Reportes JUnit/HTML locales en `/tmp/opencode/pfmdo-com-pr01-junit.xml` y `/tmp/opencode/pfmdo-com-pr01-report.html` (artefactos pesados fuera de Git). La matriz en `docs/escenario.md` conecta cada regla del MVP con su prueba.

El workflow `.github/workflows/acceptance.yml` ejecuta migración y pruebas en PR/main, falla ante regresión y sube ambos reportes incluso si fallan. [CI run #39665020146](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/actions/runs/39665020146) aprobó 121 pruebas y publicó `acceptance-reports` (JUnit/HTML). **Pendiente:** demostrar un check fallido/protección de rama (DEV-03), obtener revisión ajena y demostrar en ambiente de defensa. No cerrar #1 solo con la suite local/CI.
