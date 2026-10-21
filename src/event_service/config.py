"""Configuración de la aplicación, sin credenciales incorporadas en el código."""

import os
from collections.abc import Mapping
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class Settings(BaseModel):
    """Configuración opcional hasta que el entorno provea DB y claves de acceso.

    Ausencia de una clave no concede acceso: el módulo de autorización deberá
    rechazar el acceso protegido cuando la clave requerida sea ``None``.
    """

    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    database_url: str | None = Field(default=None, repr=False)
    event_producer_key: SecretStr | None = Field(default=None, repr=False)
    event_analyst_key: SecretStr | None = Field(default=None, repr=False)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        """Lee DATABASE_URL y las dos claves, sin valores secretos de respaldo.

        Permite inyectar un mapeo aislado en pruebas; ``None`` usa el entorno
        real. Cadenas vacías o compuestas solo por espacios equivalen a ausente.
        """
        source = os.environ if environ is None else environ

        def present(name: str) -> str | None:
            value = source.get(name)
            return value if value and value.strip() else None

        return cls(
            database_url=present("DATABASE_URL"),
            event_producer_key=present("EVENT_PRODUCER_KEY"),
            event_analyst_key=present("EVENT_ANALYST_KEY"),
        )
