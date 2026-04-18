from __future__ import annotations

from .....domain.carritos import CarritoItem
from .....domain.productos import SKU, PrecioBob


class CarritoItemMapper:
    """Materializa un CarritoItem desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> CarritoItem:
        return CarritoItem(
            sku=SKU(r["sku"]),
            nombre=r["nombre"],
            cantidad=int(r["cantidad"]),
            precio_unitario=PrecioBob(float(r["precio_bob"])),
        )
