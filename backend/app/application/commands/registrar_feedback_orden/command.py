from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RegistrarFeedbackOrdenCommand:
    """Comando: registra la opinion del cliente sobre la experiencia de compra."""

    orden_id: UUID
    sesion_id: UUID
    rating: Optional[int]
    comentario: Optional[str]
