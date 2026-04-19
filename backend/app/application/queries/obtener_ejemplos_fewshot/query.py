from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObtenerEjemplosFewShotQuery:
    """Query: top N ejemplos activos para inyectar en el system prompt."""

    limite: int = 3
