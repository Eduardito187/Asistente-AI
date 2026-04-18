from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AgregarAlCarritoCommand:
    """Comando: agregar o incrementar un SKU al carrito de una sesion."""

    sesion_id: UUID
    sku: str
    cantidad: int = 1
