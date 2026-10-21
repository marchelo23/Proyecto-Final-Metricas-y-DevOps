# ADR-0001 — Una aplicación modular para el prototipo

- **Fecha:** 2026-10-21
- **Estado:** aceptada e implementada en el MVP local; revisar con el enunciado oficial y antes del despliegue.

## Contexto y decisión

El contrato provisional pide ingesta, consulta y conteos de los mismos eventos; no hay requisitos comprobados de escala, equipos separados o aislamiento por proceso. Elegimos **una aplicación FastAPI** como unidad de ejecución, con módulos de entrada HTTP, negocio, persistencia, errores y autorización, ya implementados localmente ([vista de módulos](../arquitectura/contenedores.md)). La capacidad de negocio es autoridad lógica de `events`, no el endpoint ni el adaptador SQL. Contratos internos explícitos evitan acoplar HTTP a excepciones de DB.

## Alternativas y consecuencias

| Alternativa | Razón para no elegirla ahora |
|---|---|
| Servicios independientes de ingesta/análisis | Requeriría red, despliegues y consistencia entre procesos para el mismo dato, sin necesidad demostrada. |
| Una sola función sin fronteras internas | Menos archivos iniciales, pero diluye dueño de las reglas y mezcla validación, persistencia y respuestas HTTP. |

Ventaja: menor costo operativo y ruta clara de pruebas locales. Coste: las capacidades escalan/despliegan juntas; reevaluar si requisitos medidos justifican separarlas. La [vista de contexto](../arquitectura/contexto.md) muestra el proceso actual, no un K3s desplegado.
