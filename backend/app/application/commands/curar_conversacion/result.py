from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurarConversacionResult:
    """Resultado: id y si fue crear o actualizar."""

    id: int
    creada: bool
