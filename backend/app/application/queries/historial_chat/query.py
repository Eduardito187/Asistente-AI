from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class HistorialChatQuery:
    """Query: ultimos N mensajes de una sesion."""

    sesion_id: UUID
    limite: int = 10
