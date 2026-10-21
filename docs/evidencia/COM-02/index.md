# COM-02 — evidencia local de arquitectura (2026-10-21)

**Requisito:** [issue #2](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/2), límites, responsabilidades, decisiones y diagramas. Este registro cubre **solo** código/pruebas locales y render de vistas; no satisface todavía el contraste con Azure/K3s ni la revisión de otro integrante.

| Comprobación real | Reproducción desde la raíz | Obtenido el 2026-10-21 |
|---|---|---|
| Arquitectura, API y DB locales | `uv sync --locked`, migrar base de pruebas y `uv run --locked pytest -q --junitxml=/tmp/opencode/com02-junit.xml --html=/tmp/opencode/com02-report.html --self-contained-html` | Rama integrada: 121 pruebas aprobadas con PostgreSQL real (8 de salud + funcionalidades, persistencia, errores y acceso); resultados en evidencia COM-01/03/04/05. |
| Sintaxis y render de diagramas | Ejecutar los tres comandos fijados a Mermaid CLI 11.12.0 en [despliegue](../../arquitectura/despliegue.md). | Tres vistas del MVP integrado renderizadas de nuevo el 2026-10-21: `COM-02-contexto-final-1.svg`, `COM-02-contenedores-final-1.svg` y `COM-02-despliegue-final-1.svg` en `/tmp/opencode/`; no se commitean artefactos pesados. |

La arquitectura observada en el **código** está en [contexto](../../arquitectura/contexto.md), [contenedores](../../arquitectura/contenedores.md) y [despliegue](../../arquitectura/despliegue.md); decisiones y alternativas en [ADR-0001](../../adr/0001-descomposicion.md), [ADR-0002](../../adr/0002-almacenamiento.md) y [ADR-0003](../../adr/0003-comunicacion.md).

**Pendiente:** imágenes/registro, Azure/K3s, contraste contra manifiestos y recursos observados, revisión independiente, workflow run y demostración. PR de arquitectura: [#28](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/pull/28). No se cerró el issue.
