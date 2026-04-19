from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class FeedbackOrden:
    """Agregado FeedbackOrden: calificacion post-orden dada por el cliente."""

    id: Optional[int]
    orden_id: UUID
    sesion_id: UUID
    rating: Optional[int]
    comentario: Optional[str]
    created_at: datetime
