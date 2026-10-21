# ADR-0003 — HTTP y SQL síncronos, sin cola por defecto

- **Fecha:** 2026-10-21
- **Estado:** aceptada e implementada en el MVP local; reevaluar según el escenario oficial.

## Contexto y decisión

Para el MVP provisional el cliente necesita saber si el evento fue persistido, duplicado o inválido y consultar resultados actuales. Elegimos HTTP/JSON síncrono entre cliente y app, y SQL síncrono entre app y PostgreSQL. `POST /v1/events`, `GET /v1/events/{id}`, `GET /v1/analysis/counts` y las sondas existen y se probaron con PostgreSQL local ([contexto](../arquitectura/contexto.md)). No hay contrato de eventos asíncronos, entrega, orden ni consumidor externo.

## Alternativas y consecuencias

| Alternativa | Razón para no elegirla ahora |
|---|---|
| Cola/worker de ingesta | Exige definir acuse, entrega, deduplicación, reintentos y operación adicional; no hay requisito de procesamiento diferido. |
| HTTP entre microservicios de ingesta y análisis | Frontera de red y fallos parciales para capacidades que comparten el mismo dato sin necesidad comprobada. |

Ventaja: errores inmediatos y semántica simple para `[source, external_id]`. Costes: cliente espera a DB y una caída produce `503`; en escrituras no se reintenta automáticamente para evitar duplicación. Si el escenario exige procesamiento desacoplado o latencia/carga verificadas lo recomiendan, redactar un nuevo ADR con semántica de entrega e idempotencia antes de introducir cola. Ver también [diagrama de contenedores](../arquitectura/contenedores.md).
