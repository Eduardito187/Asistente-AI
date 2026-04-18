from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarcarCarritosAbandonadosCommand:
    """Comando: marcar como abandonadas sesiones sin actividad por N horas."""

    umbral_horas: int = 24
