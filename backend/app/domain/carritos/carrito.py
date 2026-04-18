from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from uuid import UUID

from ..productos import SKU
from .carrito_item import CarritoItem


@dataclass
class Carrito:
    """Raíz del agregado Carrito. Una Sesion tiene UN Carrito."""

    sesion_id: UUID
    items: List[CarritoItem] = field(default_factory=list)

    @property
    def total_bob(self) -> float:
        return round(sum(i.subtotal_bob for i in self.items), 2)

    @property
    def cantidad_items(self) -> int:
        return sum(i.cantidad for i in self.items)

    def esta_vacio(self) -> bool:
        return not self.items

    def tiene_sku(self, sku: SKU) -> bool:
        return any(i.sku == sku for i in self.items)
