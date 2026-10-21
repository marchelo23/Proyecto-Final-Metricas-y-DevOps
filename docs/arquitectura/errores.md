# COM-04 — validación, errores y recuperación (MVP provisional)

## Contrato e interfaces

- `EventCreate`: `source` y `type` identificadores ASCII `[A-Za-z0-9][A-Za-z0-9_-]*` (1–64); `external_id` cadena de 1–128; `occurred_at` con zona y normalizado a UTC; `payload` objeto JSON serializable, máximo **16 384 bytes** en JSON compacto UTF-8 (`ensure_ascii=False`); se rechazan campos extra. Los números no sustituyen fechas RFC3339.
- `CountsQuery`: campos HTTP `from`, `to`, `group_by=type|source`; atributo Python `from_` (alias `from`), `to`, `group_by`; fechas con zona normalizadas a UTC y `from_ < to`; se rechazan campos extra.
- `register_handlers(app: FastAPI)`: instalar **antes de iniciar** la aplicación, una vez (llamadas repetidas son inocuas). Importa de COM-02 `DuplicateEvent`, `EventNotFound`, `StorageUnavailable` desde `event_service.contracts`. No modifica `main.py`: COM-02 lo invoca. Cada respuesta incluye `X-Request-ID`; en errores coincide con `error.request_id`. Se acepta un solo ID entrante `X-Request-ID` de 1–128 caracteres ASCII alfanuméricos, `._-` tras el primero. Si falta, está duplicado o es inválido, se genera un UUID nuevo.

| Caso | HTTP | `error.code` | Verificación |
| --- | ---: | --- | --- |
| Evento/ventana válidos | 200 en pruebas de esquema HTTP; 201 en `POST /v1/events` real | — | UTC, objeto JSON y ventana `[from,to)` |
| Cuerpo, consulta o JSON inválido | 422 | `INVALID_INPUT` | Mensaje fijo; no copiar entrada a respuesta/log |
| Evento duplicado (`DuplicateEvent`) | 409 | `DUPLICATE` | La escritura previa no cambia; COM-03 garantiza unicidad DB |
| Evento ausente (`EventNotFound` o HTTP 404) | 404 | `NOT_FOUND` | No copiar ID ni detalle interno |
| Autenticación/autorización HTTP | 401 / 403 | `UNAUTHENTICATED` / `FORBIDDEN` | No copiar claves ni detalles del proveedor |
| DB caída o timeout traducido a `StorageUnavailable` | 503 | `DEPENDENCY_UNAVAILABLE` | Error público sin DSN ni mensaje de excepción |
| DB recuperada | 200 | — | Misma aplicación y proceso; consultar de nuevo |
| Error inesperado | 500 | `INTERNAL_ERROR` | Sin traceback, secretos ni cuerpo de solicitud |

Formato único: `{"error":{"code":"...","message":"texto fijo","request_id":"..."}}`. Los otros HTTP 4xx conservan su estado con `INVALID_INPUT`; otros HTTP 5xx devuelven 500 genérico. Los logs de error contienen **solo** código, estado, ID validado y plantilla de ruta del servidor (no URL real, identidad, headers, payload, excepciones ni stack). Quien llama puede correlacionar `X-Request-ID` con ese log. Evitar también access logs externos con URLs sin sanitizar. La clasificación de errores operacionales y timeouts como `StorageUnavailable`, el `pool_pre_ping=True` y el reciclado de conexiones pertenecen a COM-03; no se simula recuperación de la base en este módulo.

**Política de reintentos:** no reintentar escrituras automáticamente, ni en `errors.py` ni en capas superiores; ante 409 o 503 el cliente debe conocer el resultado antes de decidir una nueva operación. Tras volver la DB, repetir manualmente una lectura idempotente sí permite comprobar recuperación. No agregar backoff/timeout HTTP opaco que transforme un resultado de escritura desconocido en duplicados. COM-02 ya configura `connect_timeout=3` para nuevas conexiones PostgreSQL; COM-03 debe traducir fallos de conexión, ejecución y timeout a `StorageUnavailable` y verificar en integración el límite efectivo para operaciones DB. Este módulo no configura un timeout de consultas ni implementa reintentos con backoff.

**Integración COM-02/04 completada:** `/health/ready` lanza `StorageUnavailable` y utiliza estos handlers; `error.request_id` coincide con `X-Request-ID`. El stub de `errors.py` se sustituyó por la implementación COM-04. La suite integrada lo comprueba.

## Prueba real de caída y recuperación (ejecutada localmente)

Ejecutar **solo contra PostgreSQL local de pruebas**, con volumen y claves de prueba, nunca contra producción o una DB ajena. En esta máquina `docker` es wrapper de Podman y `docker compose` invoca `podman-compose`. Trabajar en el checkout integrado que contenga `compose.yaml`, migraciones y `event_service.main:app`:

1. Preparar el entorno de pruebas: definir `DATABASE_URL`, `EVENT_PRODUCER_KEY` y `EVENT_ANALYST_KEY` sin imprimir sus valores ni activar `set -x`. Elegir el nombre real del servicio PostgreSQL con `docker compose -f compose.yaml config --services` y asignarlo (`PG_SERVICE=nombre_real_del_servicio`); confirmar que `DATABASE_URL` apunta **solo** a esa base local y es accesible desde la API en el host. Ejecutar `docker compose -f compose.yaml up -d "$PG_SERVICE"` y `uv run alembic upgrade head`. Iniciar API **una sola vez** en la misma terminal y conservar su PID:

   ```bash
   uv run uvicorn event_service.main:app --host 127.0.0.1 --port 8000 &
   API_PID=$!
   kill -0 "$API_PID"
   ```

2. Definir esta sonda de lectura (no imprime claves ni cuerpo completo; necesita el rol `analyst`). Ajustar host/puerto si la API de pruebas usa otros:

   ```bash
   probe() {
     python - "$1" "$2" <<'PY'
   import json
   import os
   import sys
   from urllib.error import HTTPError
   from urllib.parse import urlencode
   from urllib.request import Request, urlopen

   expected, request_id = int(sys.argv[1]), sys.argv[2]
   query = urlencode({"from": "2020-01-01T00:00:00Z", "to": "2030-01-01T00:00:00Z", "group_by": "type"})
   request = Request(
       "http://127.0.0.1:8000/v1/analysis/counts?" + query,
       headers={"X-API-Key": os.environ["EVENT_ANALYST_KEY"], "X-Request-ID": request_id},
   )
   try:
       response = urlopen(request, timeout=10)
   except HTTPError as error:
       response = error
   with response:
       result = json.load(response)
       status = response.status
       echoed_id = response.headers["X-Request-ID"]
   assert status == expected, (status, expected)
   assert echoed_id == request_id
   if expected == 503:
       assert result["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
       assert result["error"]["request_id"] == echoed_id
   else:
       assert result["group_by"] == "type" and "total" in result
   print("status=", status, "request_id=", echoed_id, "code=", result.get("error", {}).get("code", "OK"))
   PY
   }
   ```

3. Secuencia **sin reiniciar API** (espera de hasta 30 segundos por PostgreSQL):

   ```bash
   probe 200 before-1
   docker compose -f compose.yaml stop "$PG_SERVICE"
   probe 503 down-1
   docker compose -f compose.yaml start "$PG_SERVICE"
   for attempt in $(seq 1 30); do
     if docker compose -f compose.yaml exec -T "$PG_SERVICE" sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null; then
       break
     fi
     sleep 1
   done
   probe 200 after-1
   kill -0 "$API_PID"
   ```

   Guardar estados, IDs de correlación, PID y logs sanitizados como evidencia. La prueba falla si aparece 500, se agota el timeout o requiere reiniciar la API. Recuperación de consulta **no** demuestra que sea seguro reintentar una escritura.

4. Terminar solo el proceso de API iniciado en el paso 1 (`kill "$API_PID"`); conservar el almacenamiento de prueba si se necesita evidencia de durabilidad. Reejecutar `uv run pytest -q tests/test_errors.py` en la rama integrada. **Resultado local de integración (2026-10-21):** `200 before-1 → 503 down-1 → 200 after-1`, mismo PID de API, IDs de solicitud coincidentes en cabecera/cuerpo; véase [evidencia](../evidencia/COM-04/index.md). El workflow prueba los casos automatizados, no detiene contenedores de la base durante CI.
