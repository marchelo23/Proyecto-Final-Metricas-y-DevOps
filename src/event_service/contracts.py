"""Fallos semánticos compartidos entre negocio, persistencia y borde HTTP.

Estos tipos no codifican respuestas HTTP. COM-04 asignará códigos y mensajes
públicos seguros; no propagar ``str(exc)`` de una dependencia al cliente.
"""


class EventServiceError(Exception):
    """Error esperado del dominio o de una dependencia del servicio."""


class DuplicateEvent(EventServiceError):
    """Ya existe el par (source, external_id); no se reemplaza el evento."""


class StorageUnavailable(EventServiceError):
    """No está disponible la dependencia de persistencia."""


class EventNotFound(EventServiceError):
    """No existe el evento solicitado por su identificador."""
