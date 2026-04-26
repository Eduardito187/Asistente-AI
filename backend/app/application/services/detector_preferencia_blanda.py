from __future__ import annotations

import re
from dataclasses import dataclass

from ...domain.shared.normalizacion import NormalizadorTexto

_MARCAS = (
    "samsung", "lg", "apple", "iphone", "xiaomi", "redmi",
    "hp", "lenovo", "asus", "sony", "motorola", "huawei",
    "tcl", "hisense", "toshiba", "panasonic", "mabe",
    "whirlpool", "electrolux", "bosch", "honor", "realme",
    "infinix", "tecno", "oppo", "vivo", "kalley", "microsoft",
    "acer", "dell", "jvc",
)
_PAT = "|".join(re.escape(m) for m in _MARCAS)

# "prefiero Samsung, pero si hay Xiaomi muéstramela"
# "busco Lenovo pero puedo considerar Asus o HP si conviene"
# "me gustaría LG si entra en presupuesto, si no dame alternativas"
# "quiero Samsung pero si hay opción mejor de Xiaomi inclúyela"
_RX_SOFT = re.compile(
    rf"(?P<pref>{_PAT})"                        # marca preferida
    r"[^.!?]{{0,60}}"                           # separador
    r"(?:"
    r"pero\s+(?:si\s+hay|si\s+existe|acepto|puedo\s+considerar|puedo\s+ver)"
    r"|si\s+(?:hay|existe|entra|no\s+hay\s+opciones|no\s+hay)"
    r"|aunque\s+(?:sea|podria\s+ser|prefiero\s+ver)"
    r"|tambien\s+(?:acepto|considero|podria\s+ver)"
    r"|de\s+lo\s+contrario"
    r"|si\s+no\s+(?:hay|tiene|conviene)"
    r")"
    r"[^.!?]{{0,40}}"
    rf"(?P<alt>{_PAT})",
    re.IGNORECASE,
)

# "prefiero Samsung pero si hay una mejor opción" (sin mencionar marca alternativa)
_RX_SOFT_ABIERTA = re.compile(
    rf"\bprefiero\s+(?P<pref>{_PAT})\b"
    r"[^.!?]{0,80}"
    r"\b(?:pero\s+(?:si\s+hay|acepto|puedo\s+ver)|sin\s+embargo|aunque)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PreferenciaBlanda:
    marca_preferida: str
    marca_alternativa: str | None  # None si abierta a cualquier alternativa


class DetectorPreferenciaBlanda:
    """SRP: detecta 'prefiero X pero acepto/considero Y' y variantes.

    Cuando hay preferencia blanda, la marca NO debe usarse como filtro
    duro en buscar_productos — el LLM debe mostrar ambas opciones y
    dejar que el cliente decida."""

    @classmethod
    def detectar(cls, mensaje: str | None) -> PreferenciaBlanda | None:
        if not mensaje:
            return None
        norm = NormalizadorTexto.normalizar(mensaje)
        m = _RX_SOFT.search(norm)
        if m:
            return PreferenciaBlanda(
                marca_preferida=m.group("pref").lower(),
                marca_alternativa=m.group("alt").lower(),
            )
        m2 = _RX_SOFT_ABIERTA.search(norm)
        if m2:
            return PreferenciaBlanda(
                marca_preferida=m2.group("pref").lower(),
                marca_alternativa=None,
            )
        return None
