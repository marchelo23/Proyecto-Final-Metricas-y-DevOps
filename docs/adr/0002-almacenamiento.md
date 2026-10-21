# ADR-0002 — PostgreSQL para eventos originales; conteos derivados

- **Fecha:** 2026-10-21
- **Estado:** aceptada como elección técnica del MVP, persistencia todavía no implementada (COM-03).

## Contexto y decisión

El contrato provisional exige unicidad de `(source, external_id)`, consulta por UUID, rango temporal `[from,to)` y conservación tras reiniciar app y DB con volumen. Elegimos **PostgreSQL 16**, SQLAlchemy 2 + psycopg 3 y migraciones Alembic. `events` será la fuente de verdad: evento original con `occurred_at` y `ingested_at` UTC, además de `payload` JSON. Índices y restricción única corresponderán a COM-03. Los conteos se calculan bajo demanda y no se almacenan. En este commit solo existe engine opcional para `SELECT 1` ([contenedores](../arquitectura/contenedores.md)); no hay tabla, migración, servidor DB ni prueba de reinicio.

## Alternativas y consecuencias

| Alternativa | Razón para no elegirla ahora |
|---|---|
| Sin almacén / memoria de proceso | No conserva eventos al reiniciar, incumple el objetivo provisional. |
| SQLite local | Útil en pruebas pequeñas, pero no refleja la dependencia PostgreSQL ni el reinicio compartido con volumen exigido en este MVP. |
| Almacén documental + agregaciones persistidas | Aumenta operaciones y sincronización; no justificado para filtros de fecha, unicidad y un solo agregado simple. |

Ventaja: restricciones transaccionales e índices acordes a las consultas. Costes: dependencia operativa, migraciones y gestión del volumen/backups; COM-03 debe probar reinicio y reejecución de migración. No se garantiza pérdida cero ante destrucción de la VM. Retención, tamaño y clasificación del payload quedan pendientes del escenario. El [diagrama de despliegue](../arquitectura/despliegue.md) **no** presupone un PostgreSQL provisionado.
