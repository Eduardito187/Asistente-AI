from __future__ import annotations

import re
from typing import List, Tuple

from ..texto import NormalizadorTexto
from .regla_categoria import ReglaCategoria
from .reglas_catalogo import REGLAS, SIN_CATEGORIA


class Clasificador:
    """Asigna (categoria, subcategoria) a partir de texto libre, sin estado."""

    def __init__(self, reglas: List[ReglaCategoria] = REGLAS) -> None:
        self._reglas = [
            (r.categoria, r.subcategoria, re.compile(NormalizadorTexto.sin_acentos(r.patron.lower())))
            for r in reglas
        ]

    def clasificar(self, texto: str) -> Tuple[str, str]:
        if not texto:
            return SIN_CATEGORIA
        t = NormalizadorTexto.sin_acentos(texto.lower())
        for cat, sub, rx in self._reglas:
            if rx.search(t):
                return cat, sub
        return SIN_CATEGORIA
