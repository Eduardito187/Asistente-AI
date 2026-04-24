from __future__ import annotations

from ....domain.productos import Producto


class ProductoSerializer:
    """Proyecciones JSON-friendly del agregado Producto para el LLM."""

    _CAMPOS_ATRIBUTOS = (
        "pulgadas", "capacidad_gb", "ram_gb", "capacidad_litros", "capacidad_kg",
        "potencia_w", "procesador", "color", "tipo_panel", "resolucion",
        "bateria_mah", "camara_mp", "camara_frontal_mp", "soporta_5g",
        "sistema_operativo", "refresh_hz", "gpu",
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
        if p.modelo:
            base["modelo"] = p.modelo
        if p.meses_garantia:
            base["meses_garantia"] = p.meses_garantia
        if p.es_descontinuado:
            base["es_descontinuado"] = True
            base["solo_tienda_fisica"] = True
        atributos = cls._atributos_presentes(p)
        if atributos:
            base["atributos"] = atributos
        return base

    _MAX_DESCRIPCION = 400
    _MAX_CARACTERISTICAS = 300

    @classmethod
    def detalle(cls, p: Producto) -> dict:
        """Proyeccion extendida con descripcion e imagen para vistas detalle.

        La descripcion se recorta a `_MAX_DESCRIPCION` caracteres — algunas
        descripciones reales del catalogo tienen 2000+ caracteres, saturan
        el ancho de banda y el contexto del LLM sin aportar valor. Si el
        cliente quiere el detalle completo, el endpoint /productos/{sku} lo
        devuelve intacto."""
        base = cls.resumen(p)
        base["descripcion"] = cls._recortar(p.descripcion, cls._MAX_DESCRIPCION)
        base["imagen_url"] = p.imagen_url
        if p.caracteristicas:
            base["caracteristicas"] = cls._recortar(p.caracteristicas, cls._MAX_CARACTERISTICAS)
        return base

    @staticmethod
    def _recortar(texto: str | None, limite: int) -> str | None:
        if not texto:
            return texto
        if len(texto) <= limite:
            return texto
        return texto[:limite].rstrip() + "…"

    @classmethod
    def _atributos_presentes(cls, p: Producto) -> dict:
        return {campo: getattr(p, campo) for campo in cls._CAMPOS_ATRIBUTOS if getattr(p, campo) is not None}
