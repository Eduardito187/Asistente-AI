from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VaciarCarritoCommand:
    """Comando: vaciar el carrito completo de una sesion."""

    sesion_id: UUID
