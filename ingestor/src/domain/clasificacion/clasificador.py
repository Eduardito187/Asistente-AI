from __future__ import annotations

import re
from typing import List, Tuple

from ..texto import NormalizadorTexto
from .mapa_marca import MapaMarca
from .mapa_product_type import MapaProductType
from .regla_categoria import ReglaCategoria
from .reglas_catalogo import REGLAS, SIN_CATEGORIA


class Clasificador:
    """Asigna (categoria, subcategoria) a un producto.

    Estrategia en cascada:
    1. Si el feed trae un `product_type` especifico conocido, usarlo directo.
    2. Si no, aplicar reglas regex sobre el NOMBRE (no descripcion) en orden.
    3. Si nada matchea, intentar fallback por marca mono-categoria.
    4. Si nada matchea, devolver SIN_CATEGORIA.

    Usar solo el nombre para las reglas evita que soportes, fundas o cables
    caigan en la categoria del producto que describen ("tv", "televisor"
    aparecen en sus descripciones).
    """

    def __init__(self, reglas: List[ReglaCategoria] = REGLAS) -> None:
        self._reglas = [
            (r.categoria, r.subcategoria, re.compile(NormalizadorTexto.sin_acentos(r.patron.lower())))
            for r in reglas
        ]

    def clasificar(
        self,
        nombre: str,
        product_type: str | None = None,
        marca: str | None = None,
    ) -> Tuple[str, str]:
        mapeo = MapaProductType.resolver(product_type)
        if mapeo is not None:
            return mapeo
        if nombre:
            t = NormalizadorTexto.sin_acentos(nombre.lower())
            for cat, sub, rx in self._reglas:
                if rx.search(t):
                    return cat, sub
        mapeo_marca = MapaMarca.resolver(marca)
        if mapeo_marca is not None:
            return mapeo_marca
        return SIN_CATEGORIA
