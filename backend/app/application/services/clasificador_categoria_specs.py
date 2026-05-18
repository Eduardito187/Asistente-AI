from __future__ import annotations


class ClasificadorCategoriaSpecs:
    """SRP: decide qué specs de perfil son compatibles con una categoria.

    Previene que specs de computación (SSD/RAM/GPU) bloqueen búsquedas
    de electrodomésticos, y que pulgadas de TV bloqueen búsquedas de
    laptops con otra resolución de pantalla."""

    _CATS_COMPUTACION = frozenset({
        "computación", "computacion", "laptops", "celulares",
        "tablets", "gaming",
    })
    _CATS_PANTALLA = frozenset({
        "computación", "computacion", "laptops", "celulares", "tablets",
        "televisores", "gaming", "fotografía", "fotografia",
    })

    @classmethod
    def es_computacion(cls, categoria: str) -> bool:
        return (categoria or "").strip().lower() in cls._CATS_COMPUTACION

    @classmethod
    def tiene_pantalla(cls, categoria: str) -> bool:
        return (categoria or "").strip().lower() in cls._CATS_PANTALLA
