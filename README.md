# Proyecto Final — Métricas y DevOps

Repositorio de trabajo del proyecto final. El backlog está compuesto por **27 issues** que cubren los requisitos evaluables de los grupos **3.1 Aplicación y arquitectura**, **3.2 DevOps** y **3.3 Métricas de Software y observabilidad**, cada uno con su evidencia mínima, trabajo propuesto, criterios de aceptación y Definition of Done.

> **Nombre del repositorio:** GitHub no admite espacios en el nombre, por lo que normalizó el solicitado *"Proyecto Final Metricas y DevOps"* a `Proyecto-Final-Metricas-y-DevOps`. Esta es la URL canónica.

- **URL:** <https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps>
- **Milestones:** `3.1 Aplicación y arquitectura`, `3.2 DevOps` y `3.3 Métricas de Software y observabilidad`
- **Estado:** backlog inicial creado; el esqueleto técnico COM-02 implementa configuración y salud, no ingesta ni análisis funcionales.

## Arranque local del esqueleto COM-02

Requiere Python 3.12 o 3.13 y [`uv`](https://docs.astral.sh/uv/). Desde la raíz del repositorio:

```bash
uv sync --group dev
uv run uvicorn event_service.main:app --host 127.0.0.1 --port 8000
```

`GET http://127.0.0.1:8000/health/live` devuelve `200`. `GET /health/ready` devuelve `503` sin `DATABASE_URL`; con una URL `postgresql+psycopg://...` **aportada por el entorno** verifica `SELECT 1` y devuelve `200` solo si PostgreSQL responde. No se incluyen credenciales ni se crea automáticamente la base o sus tablas. `EVENT_PRODUCER_KEY` y `EVENT_ANALYST_KEY` se leerán del entorno para el control de acceso futuro; hoy no hay rutas protegidas implementadas.

```bash
uv run pytest
# Opcional: evidencia local fuera del repositorio
uv run pytest --junitxml=/tmp/opencode/event-service-junit.xml --html=/tmp/opencode/event-service-report.html --self-contained-html
```

La [arquitectura implementada](docs/arquitectura/contexto.md) y los [ADRs](docs/adr/0001-descomposicion.md) separan lo que ya existe de lo pendiente; Azure, K3s y registro de imágenes **no están desplegados** por este cambio.

## Backlog

### 3.1 Aplicación y arquitectura

| ID | Requisito | Evidencia mínima | Issue |
|---|---|---|---|
| COM-01 | Implementar las funciones y reglas del escenario | Pruebas de aceptación ejecutables y resultados verificables | [#1](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/1) |
| COM-02 | Definir y justificar límites y responsabilidades | Diagrama de arquitectura real y decisiones | [#2](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/2) |
| COM-03 | Persistir la información exigida | Persistencia ante reinicio de componentes | [#3](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/3) |
| COM-04 | Manejar errores y validar entradas | Pruebas positivas, negativas y de recuperación | [#4](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/4) |
| COM-05 | Controles de acceso cuando corresponda | Pruebas de acceso autorizado y rechazado | [#5](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/5) |
| COM-06 | Trade-offs de consistencia, disponibilidad, costo y complejidad | Registro de decisiones y alternativas descartadas | [#6](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/6) |

### 3.2 DevOps

| ID | Requisito | Evidencia mínima | Issue |
|---|---|---|---|
| DEV-01 | Versionar aplicación, infraestructura y configuración no secreta | Repositorio e historial con PRs revisados | [#7](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/7) |
| DEV-02 | Distribuir componentes como imágenes de contenedor | Dockerfiles, imágenes versionadas y trazables | [#8](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/8) |
| DEV-03 | Integración continua con GitHub Actions | Checks en PR y protección de rama | [#9](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/9) |
| DEV-04 | Automatizar build y publicación de imágenes | Vínculo commit → workflow → imagen | [#10](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/10) |
| DEV-05 | Entrega controlada con validación y producción separadas | Workflow, aprobaciones y despliegue | [#11](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/11) |
| DEV-06 | Recursos principales de Azure con Terraform | Código, plan revisable y apply controlado | [#12](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/12) |
| DEV-07 | Estado remoto de Terraform protegido | Backend y procedimiento de inicialización | [#13](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/13) |
| DEV-08 | Validación de Terraform en GitHub Actions | Validación y plan sin apply en PRs no aprobados | [#14](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/14) |
| DEV-09 | Instalar y operar K3s en VM de Azure | Nodos y workloads verificables | [#15](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/15) |
| DEV-10 | Separar configuración y secretos; privilegio mínimo | Configuración, secretos y evidencia de permisos | [#16](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/16) |
| DEV-11 | Salud y recursos de los workloads | Probes, requests y límites justificados | [#17](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/17) |
| DEV-12 | Recuperar una versión funcional tras un despliegue defectuoso | Demostración de rollback y verificación | [#18](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/18) |
| DEV-13 | Reconstruir el ambiente con procedimiento documentado | Instrucciones y prerrequisitos explícitos | [#19](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/19) |
| DEV-14 | Consumo de Azure bajo US$100 | Estimación, cargos, alertas y detención/eliminación | [#20](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/20) |

### 3.3 Métricas de Software y observabilidad

| ID | Requisito | Evidencia mínima | Issue |
|---|---|---|---|
| MET-01 | Definir indicadores técnicos y de comportamiento | Catálogo con definición, unidad, fuente, cálculo y propósito | [#21](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/21) |
| MET-02 | Incorporar logs estructurados | Registros con identificadores de correlación | [#22](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/22) |
| MET-03 | Instrumentar métricas de aplicación e infraestructura | Consultas y series temporales verificables | [#23](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/23) |
| MET-04 | Instrumentar trazas con OpenTelemetry | Trazas consultables y correlación entre señales | [#24](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/24) |
| MET-05 | Construir dashboards para preguntas operativas | Paneles interpretables con unidades y ventanas | [#25](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/25) |
| MET-06 | Configurar alertas justificadas | Regla, activación y análisis de falsos positivos | [#26](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/26) |
| MET-07 | Analizar una degradación inducida y su recuperación | Secuencia temporal, evidencia, interpretación y límites | [#27](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/27) |

> **Anexo II, sección 8.2:** el detalle definitivo de indicadores y señales está en ese anexo. Si existe diferencia de redacción con este backlog, prevalece el anexo. Instalar una herramienta de monitoreo no satisface por sí solo los requisitos MET.

## Cómo se trabaja el backlog

1. Tomar un issue y moverlo a **In progress** en el Project o tablero del equipo.
2. Crear una rama desde `main` con el ID del requisito.
3. Implementar y adjuntar la evidencia en el issue (enlace a PR, workflow run, captura, log o documento).
4. Abrir un PR que referencie el issue y completar la plantilla de revisión.
5. Con checks en verde y al menos una revisión, integrar a `main`.
6. Cerrar el issue solo cuando el Definition of Done esté completo y la evidencia esté enlazada.

### Ramas y commits

| Tipo | Patrón | Ejemplo |
|---|---|---|
| Funcionalidad | `feat/<ID>-<descripcion>` | `feat/COM-01-reglas-escenario` |
| Infraestructura | `infra/<ID>-<descripcion>` | `infra/DEV-06-terraform-azure` |
| CI/CD | `ci/<ID>-<descripcion>` | `ci/DEV-03-github-actions` |
| Observabilidad | `obs/<ID>-<descripcion>` | `obs/MET-03-metricas-app` |
| Documentación | `docs/<ID>-<descripcion>` | `docs/COM-02-arquitectura` |
| Corrección | `fix/<ID>-<descripcion>` | `fix/COM-04-validacion-fechas` |

Se usa [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `infra:`, `ci:`, `docs:`, `test:`, `chore:`.

### Evidencia

La evidencia vive en `docs/evidencia/<ID>/` cuando es texto o captura pequeña; los artefactos pesados (reportes, SBOM, planes de Terraform) se publican como artefactos del workflow y se enlazan desde el issue. Convenciones en [`docs/evidencia/README.md`](docs/evidencia/README.md).

## Etiquetas

| Etiqueta | Uso |
|---|---|
| `grupo:aplicacion` | Requisitos COM (3.1) |
| `grupo:devops` | Requisitos DEV (3.2) |
| `grupo:metricas` | Requisitos MET (3.3) |
| `tipo:requisito` | Issue evaluable en la defensa |
| `evidencia:defensa` | Produce evidencia verificable |

## Alcance y supuestos

- No hay una cantidad obligatoria de microservicios, bases de datos, colas, frameworks, VMs ni herramientas de monitoreo; la implementación responde al escenario.
- En 3.3 no basta con instalar una herramienta: se exigen indicadores, señales correlacionadas, dashboards, alertas y análisis de degradación según el Anexo II, sección 8.2.
- Se admite un solo nodo K3s y no se exige alta disponibilidad entre zonas ni tolerancia a la pérdida total de la VM.
- La inicialización mínima de identidades y del backend de estado puede ser manual, pero debe estar documentada y justificada (DEV-07 y DEV-13).
- El ambiente se apaga o elimina cuando no se usa para mantener el consumo bajo US$100 (DEV-14).
