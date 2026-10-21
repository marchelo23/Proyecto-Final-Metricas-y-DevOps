# COM-02 — evidencia local del esqueleto (2026-10-21)

**Requisito:** [issue #2](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/2), límites, responsabilidades, decisiones y diagramas. Este registro cubre **solo** ejecución de la base local y render de las vistas; no satisface todavía el contraste con el ambiente de defensa.

| Comprobación real | Reproducción desde la raíz | Obtenido el 2026-10-21 |
|---|---|---|
| Rutas de salud/configuración | `uv sync --group dev` y `uv run pytest -q --junitxml=/tmp/opencode/com-02-junit.xml --html=/tmp/opencode/com-02-report.html --self-contained-html` | 8 pruebas aprobadas; 1 advertencia de deprecación de `starlette.testclient`/`httpx` en dependencias. DB simulada o ausente: no prueba PostgreSQL real. Informes locales fuera de Git. |
| Sintaxis y render de diagramas | Ejecutar los tres comandos fijados a Mermaid CLI 11.12.0 en [despliegue](../../arquitectura/despliegue.md). | 1 diagrama renderizado por cada Markdown (`contexto`, `contenedores`, `despliegue`) en SVG/Markdown bajo `/tmp/opencode/`. |

La arquitectura observada en el **código** está en [contexto](../../arquitectura/contexto.md), [contenedores](../../arquitectura/contenedores.md) y [despliegue](../../arquitectura/despliegue.md); decisiones y alternativas en [ADR-0001](../../adr/0001-descomposicion.md), [ADR-0002](../../adr/0002-almacenamiento.md) y [ADR-0003](../../adr/0003-comunicacion.md).

**Pendiente:** ingesta/análisis funcional, migración, PostgreSQL real, imágenes/registro, Azure/K3s, contraste contra manifiestos y recursos observados, revisión independiente, workflow/PR y demostración. No se enlazó PR o run ni se cerró el issue: no existen todavía en este cambio.
