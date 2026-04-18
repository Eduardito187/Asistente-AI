from __future__ import annotations

from ....domain.productos import Producto


class ProductoSerializer:
    """Proyecciones JSON-friendly del agregado Producto para el LLM."""

    @staticmethod
    def resumen(p: Producto) -> dict:
        """Proyeccion minima para citas y listados."""
        return {
            "sku": str(p.sku),
            "nombre": p.nombre,
            "categoria": p.categoria,
            "subcategoria": p.subcategoria,
            "marca": p.marca,
            "precio_bob": p.precio.monto,
            "precio_anterior_bob": p.precio_anterior.monto if p.precio_anterior else None,
            "stock": p.stock,
        }

    @classmethod
    def detalle(cls, p: Producto) -> dict:
        """Proyeccion extendida con descripcion e imagen para vistas detalle."""
        base = cls.resumen(p)
        base["descripcion"] = p.descripcion
        base["imagen_url"] = p.imagen_url
        return base
