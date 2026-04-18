from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VerCarritoQuery:
    """Query: obtener el carrito actual de una sesion."""

    sesion_id: UUID
