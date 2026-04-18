from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class QuitarDelCarritoCommand:
    """Comando: remover un SKU del carrito de una sesion."""

    sesion_id: UUID
    sku: str
