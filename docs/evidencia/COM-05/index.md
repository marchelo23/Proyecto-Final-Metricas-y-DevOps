# COM-05 — Evidencia local parcial (MVP)

**Criterio:** el MVP de ingesta y análisis de eventos restringe la creación a `producer` y las consultas a `analyst`. Claves ausentes/inválidas → 401; credencial válida del otro rol → 403. Los roles son una decisión explícita del MVP para el tema y los requisitos comunes recibidos. Véase [matriz de acceso](../../arquitectura/acceso.md) y el [issue #5](https://github.com/marchelo23/Proyecto-Final-Metricas-y-DevOps/issues/5).

## Reproducción local

```bash
PYTHONPATH=src python3 -m pytest -q tests/test_auth.py
```

**Esperado:** las pruebas de credenciales, permisos por ruta y por función de negocio, configuración incompleta y ausencia de filtración de claves pasan. **Obtenido (2026-10-21, integración local):** `34 passed in 1.48s`. Los casos usan una aplicación FastAPI mínima; no sustituyen las pruebas del servicio integrado ni del ambiente de defensa.

## Pendiente para cerrar el issue

- Ejecutar la suite sobre la aplicación integrada, conservar un workflow run y enlazar un PR revisado por otra persona desde el issue.
- Verificar despliegue y rotación/gestión real de secretos en el ambiente de defensa. Las claves reales no se publican en Git.
- Si el alcance futuro introduce propiedad individual de eventos, añadir y probar aislamiento entre propietarios. Actualmente no hay recursos individuales por usuario.

No se afirma despliegue, PR, workflow ejecutado ni revisión ajena. No cerrar el issue con esta evidencia parcial.
