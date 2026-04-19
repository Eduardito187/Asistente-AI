from __future__ import annotations

from dataclasses import dataclass

from .intencion import Intencion


@dataclass(frozen=True)
class RespuestaIntencionDirecta:
    """Respuesta pre-generada que permite saltarse el loop tool-calling."""

    intencion: Intencion
    texto: str
