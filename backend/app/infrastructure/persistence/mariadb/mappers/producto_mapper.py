from __future__ import annotations

from .....domain.productos import SKU, PrecioBob, Producto


class ProductoMapper:
    """Materializa un Producto desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> Producto:
        return Producto(
            sku=SKU(r["sku"]),
            nombre=r["nombre"],
            descripcion=r.get("descripcion"),
            categoria=r.get("categoria"),
            subcategoria=r.get("subcategoria"),
            marca=r.get("marca"),
            precio=PrecioBob(float(r["precio_bob"])),
            precio_anterior=(
                PrecioBob(float(r["precio_anterior_bob"]))
                if r.get("precio_anterior_bob") is not None
                else None
            ),
            stock=int(r.get("stock") or 0),
            imagen_url=r.get("imagen_url"),
            activo=bool(r.get("activo")),
        )
