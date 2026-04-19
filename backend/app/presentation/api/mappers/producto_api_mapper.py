from __future__ import annotations

from ....domain.productos import Producto
from ..schemas import ProductoOut


class ProductoApiMapper:
    """Convierte Productos de dominio a DTOs Pydantic de la API."""

    @staticmethod
    def out(p: Producto) -> ProductoOut:
        return ProductoOut(
            sku=str(p.sku),
            nombre=p.nombre,
            descripcion=p.descripcion,
            categoria=p.categoria,
            subcategoria=p.subcategoria,
            marca=p.marca,
            precio_bob=p.precio.monto,
            precio_anterior_bob=p.precio_anterior.monto if p.precio_anterior else None,
            imagen_url=p.imagen_url,
            activo=p.activo,
        )
