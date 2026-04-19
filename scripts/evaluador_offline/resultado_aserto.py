from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoAserto:
    """Veredicto de un unico aserto de un turno dorado."""

    nombre: str
    ok: bool
    detalle: str = ""
