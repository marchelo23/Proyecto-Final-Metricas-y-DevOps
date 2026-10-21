# ADR-0002 — PostgreSQL para eventos originales; conteos derivados

- **Fecha:** 2026-10-21
- **Estado:** aceptada e implementada localmente en COM-03; despliegue/backup de defensa pendientes.

## Contexto y decisión

El contrato provisional exige unicidad de `(source, external_id)`, consulta por UUID, rango temporal `[from,to)` y conservación tras reiniciar app y DB con volumen. Elegimos **PostgreSQL 16**, SQLAlchemy 2 + psycopg 3 y migraciones Alembic. `events` es fuente de verdad: evento original con `occurred_at` y `ingested_at` UTC, además de `payload` JSONB. COM-03 implementa índice temporal, restricción única, tabla, migración y prueba de reinicio sobre PostgreSQL real. Los conteos se calculan bajo demanda y no se almacenan ([módulos](../arquitectura/contenedores.md)).

## Alternativas y consecuencias

| Alternativa | Razón para no elegirla ahora |
|---|---|
| Sin almacén / memoria de proceso | No conserva eventos al reiniciar, incumple el objetivo provisional. |
| SQLite local | Útil en pruebas pequeñas, pero no refleja la dependencia PostgreSQL ni el reinicio compartido con volumen exigido en este MVP. |
| Almacén documental + agregaciones persistidas | Aumenta operaciones y sincronización; no justificado para filtros de fecha, unicidad y un solo agregado simple. |

Ventaja: restricciones transaccionales e índices acordes a las consultas. Costes: dependencia operativa, migraciones y gestión del volumen/backups. El reinicio y reejecución de migración se probaron localmente; no se garantiza pérdida cero ante destrucción de la VM. Retención y clasificación del payload quedan pendientes del escenario. El [despliegue](../arquitectura/despliegue.md) muestra solo PostgreSQL local, no Azure/K3s.
