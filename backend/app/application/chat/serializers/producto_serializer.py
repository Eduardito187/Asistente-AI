from __future__ import annotations

from ....domain.productos import Producto


class ProductoSerializer:
    """Proyecciones JSON-friendly del agregado Producto para el LLM."""

    _CAMPOS_ATRIBUTOS = (
        "pulgadas", "capacidad_gb", "ram_gb", "capacidad_litros", "capacidad_kg",
        "potencia_w", "procesador", "color", "tipo_panel", "resolucion",
    )

    @classmethod
    def resumen(cls, p: Producto) -> dict:
        """Proyeccion minima para citas y listados. No incluye stock a proposito:
        el asistente filtra siempre por disponibilidad y el cliente no lo necesita ver."""
        base = {
            "sku": str(p.sku),
            "nombre": p.nombre,
            "categoria": p.categoria,
            "subcategoria": p.subcategoria,
            "marca": p.marca,
            "precio_bob": p.precio.monto,
            "precio_anterior_bob": p.precio_anterior.monto if p.precio_anterior else None,
        }
        atributos = cls._atributos_presentes(p)
        if atributos:
            base["atributos"] = atributos
        return base

    @classmethod
    def detalle(cls, p: Producto) -> dict:
        """Proyeccion extendida con descripcion e imagen para vistas detalle."""
        base = cls.resumen(p)
        base["descripcion"] = p.descripcion
        base["imagen_url"] = p.imagen_url
        return base

    @classmethod
    def _atributos_presentes(cls, p: Producto) -> dict:
        return {campo: getattr(p, campo) for campo in cls._CAMPOS_ATRIBUTOS if getattr(p, campo) is not None}
