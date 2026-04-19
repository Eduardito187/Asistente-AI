from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class ResultadoBuscarOrdenSinFeedback:
    """DTO: id de la orden sin feedback (o None)."""

    orden_id: Optional[UUID]
