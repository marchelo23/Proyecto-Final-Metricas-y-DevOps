# Acceso provisional del MVP (COM-05)

Esta es una **decisión provisional del MVP**, no una afirmación de que el escenario original exija estos roles. La aplicación usa dos claves de API distintas, enviadas en el encabezado `X-API-Key`. Las claves se leen de `EVENT_PRODUCER_KEY` y `EVENT_ANALYST_KEY` en el entorno del proceso; no se incluyen en Git, imágenes, clientes, respuestas ni logs.

| Operación | `producer` | `analyst` | Sin clave o clave incorrecta |
|---|---|---|---|
| `POST /v1/events` (`events:create`) | Permitida | 403 | 401 |
| `GET /v1/events/{id}` (`events:read`) | 403 | Permitida | 401 |
| `GET /v1/analysis/counts` (`analysis:read`) | 403 | Permitida | 401 |
| `GET /health/live`, `GET /health/ready` | Pública | Pública | Pública |

`require_producer` y `require_analyst` son dependencias FastAPI para verificar la clave y el rol **en cada ruta protegida**; devuelven un `Principal(role=...)`. La función propietaria de cada operación debe llamar también a `ensure_permission(principal, action)` antes de efectuarla, incluso si la ruta ya verificó el rol. Una clave válida de otro rol produce 403; una ausente o incorrecta produce 401. Si falta alguna de las dos claves de entorno, está vacía (o sólo contiene espacios), o ambas claves son idénticas, **ningún rol** puede autenticarse. Las comparaciones de claves usan `compare_digest`. Los detalles de error son genéricos; el formateo del error HTTP común corresponde al manejador de errores de la aplicación.

Las pruebas en `tests/test_auth.py` comprueban permisos por ruta y por servicio, claves inexistentes o inválidas, configuración incompleta, claves iguales y escalamiento vertical (uso de una clave válida contra operaciones del otro rol). **No existe propiedad individual de eventos ni aislamiento por usuario en este MVP**, así que no aplica una prueba de escalamiento lateral; deberá agregarse si se incorporan recursos con propietario individual. Estos controles son de aplicación y no sustituyen TLS, gestión/rotación de secretos ni controles de red del despliegue.
