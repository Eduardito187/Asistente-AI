from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObtenerOrdenQuery:
    """Query: obtener una orden por su numero (DSM-xxxxxx)."""

    numero_orden: str
