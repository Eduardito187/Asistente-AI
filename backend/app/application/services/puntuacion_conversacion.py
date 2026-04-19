from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PuntuacionConversacion:
    """Resultado numerico del `EvaluadorConversacion`."""

    score: int
    turnos: int
    llevo_a_orden: bool
    motivos: list[str]

    @property
    def es_buena(self) -> bool:
        return self.score >= 50
