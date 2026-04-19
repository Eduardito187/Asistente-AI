from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivarConversacionCuradaCommand:
    """Comando: activa/desactiva una conversacion curada para el few-shot."""

    id: int
    activa: bool
