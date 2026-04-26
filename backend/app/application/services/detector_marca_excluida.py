from __future__ import annotations

import re

from ...domain.shared.normalizacion import NormalizadorTexto

_MARCAS_CATALOGO = (
    "samsung", "lg", "apple", "iphone", "xiaomi", "redmi",
    "hp", "lenovo", "asus", "sony", "motorola", "moto",
    "huawei", "nokia", "tcl", "hisense", "toshiba",
    "panasonic", "mabe", "whirlpool", "electrolux",
    "bosch", "beko", "honor", "realme", "infinix",
    "tecno", "oppo", "vivo", "kalley", "microsoft",
    "acer", "dell", "jvc", "aiwa", "blackview",
)

_PATRON_MARCAS = "|".join(re.escape(m) for m in _MARCAS_CATALOGO)

_RX_MARCA_EXCLUIDA = re.compile(
    rf"\b(?:"
    rf"pero\s+no|no\s+quiero|no\s+(?:me\s+)?(?:muestres?|pongas?|traigas?|recomiendes?)|"
    rf"que\s+no\s+(?:sea|sean)|sin|excepto|excluye|descarta|fuera\s+(?:de\s+)?la\s+marca"
    rf")"
    rf"\s+(?:la\s+marca\s+)?(?:una?\s+|el\s+|la\s+)?({_PATRON_MARCAS})\b",
    re.IGNORECASE,
)


class DetectorMarcaExcluida:
    """SRP: detecta marcas que el cliente quiere EXCLUIR explícitamente.
    Devuelve lista normalizada de marcas a filtrar via marca_excluye en
    BuscarProductosQuery.

    Cubre patrones:
      - "quiero celular pero no Samsung"
      - "sin LG", "excepto Xiaomi"
      - "que no sea HP", "no quiero Lenovo"
      - "no me muestres Asus"
    """

    @classmethod
    def detectar(cls, mensaje: str | None) -> list[str]:
        if not mensaje:
            return []
        norm = NormalizadorTexto.normalizar(mensaje)
        return sorted({
            m.group(1).lower()
            for m in _RX_MARCA_EXCLUIDA.finditer(norm)
        })
