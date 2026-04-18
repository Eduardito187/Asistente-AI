from __future__ import annotations

from .....domain.ordenes import OrdenItem
from .....domain.productos import SKU, PrecioBob


class OrdenItemMapper:
    """Materializa un OrdenItem desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> OrdenItem:
        return OrdenItem(
            sku=SKU(r["sku"]),
            nombre=r["nombre"],
            marca=r.get("marca"),
            cantidad=int(r["cantidad"]),
            precio_unitario=PrecioBob(float(r["precio_unitario_bob"])),
        )
