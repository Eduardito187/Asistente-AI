from __future__ import annotations

from .producto import Producto


class ProductoGraphqlMapper:
    """Mapea filas crudas de la tabla productos a tipos GraphQL."""

    @staticmethod
    def from_row(r: dict) -> Producto:
        return Producto(
            sku=r["sku"],
            nombre=r["nombre"],
            descripcion=r["descripcion"],
            categoria=r["categoria"],
            marca=r["marca"],
            precio_bob=float(r["precio_bob"]),
            precio_anterior_bob=(
                float(r["precio_anterior_bob"])
                if r["precio_anterior_bob"] is not None
                else None
            ),
            stock=int(r["stock"]),
            imagen_url=r["imagen_url"],
            activo=bool(r["activo"]),
        )
