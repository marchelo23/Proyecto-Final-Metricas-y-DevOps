# ADR-0001 — Una aplicación modular para el prototipo

- **Fecha:** 2026-10-21
- **Estado:** aceptada para el prototipo COM-02; revisar con el enunciado oficial y al integrar COM-01.

## Contexto y decisión

El contrato provisional pide ingesta, consulta y conteos de los mismos eventos; no hay requisitos comprobados de escala, equipos separados o aislamiento por proceso. Elegimos **una aplicación FastAPI** como unidad de ejecución, con módulos de entrada HTTP, negocio, persistencia, errores y autorización. Por ahora solo están operativos composición/configuración/salud; otros módulos son stubs o aún no existen ([vista real](../arquitectura/contenedores.md)). La capacidad de negocio será la autoridad lógica de `events`, no el endpoint ni el adaptador SQL. Mantener contratos internos explícitos evita acoplar HTTP a excepciones de DB.

## Alternativas y consecuencias

| Alternativa | Razón para no elegirla ahora |
|---|---|
| Servicios independientes de ingesta/análisis | Requeriría red, despliegues y consistencia entre procesos para el mismo dato, sin necesidad demostrada. |
| Una sola función sin fronteras internas | Menos archivos iniciales, pero diluye dueño de las reglas y mezcla validación, persistencia y respuestas HTTP. |

Ventaja: menor costo operativo y ruta clara de pruebas locales. Coste: las capacidades escalan/despliegan juntas; reevaluar si requisitos medidos justifican separarlas. La [vista de contexto](../arquitectura/contexto.md) distingue contratos planificados del único proceso actual. No es una afirmación sobre K3s desplegado.
