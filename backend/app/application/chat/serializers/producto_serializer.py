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

    _MAX_DESCRIPCION = 400

    @classmethod
    def detalle(cls, p: Producto) -> dict:
        """Proyeccion extendida con descripcion e imagen para vistas detalle.

        La descripcion se recorta a `_MAX_DESCRIPCION` caracteres — algunas
        descripciones reales del catalogo tienen 2000+ caracteres, saturan
        el ancho de banda y el contexto del LLM sin aportar valor. Si el
        cliente quiere el detalle completo, el endpoint /productos/{sku} lo
        devuelve intacto."""
        base = cls.resumen(p)
        base["descripcion"] = cls._recortar(p.descripcion)
        base["imagen_url"] = p.imagen_url
        return base

    @classmethod
    def _recortar(cls, texto: str | None) -> str | None:
        if not texto:
            return texto
        if len(texto) <= cls._MAX_DESCRIPCION:
            return texto
        return texto[: cls._MAX_DESCRIPCION].rstrip() + "…"

    @classmethod
    def _atributos_presentes(cls, p: Producto) -> dict:
        return {campo: getattr(p, campo) for campo in cls._CAMPOS_ATRIBUTOS if getattr(p, campo) is not None}
