from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class NegativePattern:
    """Patron prohibido (#19 del review). Se materializan como reglas
    deterministicas, NO como few-shots.

    Ejemplos:
      - 'usuario pide laptop, no recomendar celulares'
      - 'usuario pide ingenieria, no Chromebook'
      - 'usuario pide GPU dedicada, no asumir por i7'"""

    id: Optional[int]
    patron: str
    reason_code: Optional[str]
    descripcion: Optional[str]
    activo: bool
    ocurrencias_observadas: int
    created_at: Optional[datetime] = None
