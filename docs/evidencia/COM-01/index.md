# COM-01 — Evidencia local del MVP de eventos

**Criterio:** las funciones y reglas del [MVP provisional](../../escenario.md) tienen pruebas de aceptación trazables. El detalle del escenario oficial «Ingesta y análisis de eventos» no se recibió; no se afirma cobertura de funciones que todavía no conocemos. Véase [issue #1](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/1).

## Reproducir desde una base PostgreSQL de pruebas

Con `TEST_DATABASE_URL=DATABASE_URL` apuntando exclusivamente a una base `*_test`, claves de prueba en `EVENT_PRODUCER_KEY`/`EVENT_ANALYST_KEY` y PostgreSQL 16 en marcha:

```bash
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked pytest --junitxml=/tmp/opencode/com01-junit.xml --html=/tmp/opencode/com01-report.html --self-contained-html
```

**Esperado:** ingesta, consulta, agregación por tiempo/tipo/fuente, unicidad, validaciones y autorización pasan; la suite falla si falla un caso. **Obtenido (2026-10-21, rama integrada):** `121 passed, 7 warnings`; 23 casos en `tests/test_acceptance.py` ejecutados contra la API real con PostgreSQL. Reportes JUnit/HTML locales en `/tmp/opencode/pfmdo-com-pr01-junit.xml` y `/tmp/opencode/pfmdo-com-pr01-report.html` (artefactos pesados fuera de Git). La matriz en `docs/escenario.md` conecta cada regla del MVP con su prueba.

El workflow `.github/workflows/acceptance.yml` ejecuta migración y pruebas en PR/main, falla ante regresión y sube ambos reportes incluso si fallan. **Pendiente:** enlazar el workflow run real cuando GitHub lo ejecute, probar un fallo deliberado en PR, obtener revisión ajena y demostrar en ambiente de defensa. No cerrar #1 solo con la suite local ni atribuir el MVP al enunciado oficial.
