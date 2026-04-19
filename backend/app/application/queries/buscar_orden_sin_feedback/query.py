from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BuscarOrdenSinFeedbackQuery:
    """Query: devuelve la ultima orden de la sesion que aun no tiene feedback."""

    sesion_id: UUID
