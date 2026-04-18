from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VerOrdenesSesionQuery:
    """Query: listar todas las ordenes de una sesion."""

    sesion_id: UUID
