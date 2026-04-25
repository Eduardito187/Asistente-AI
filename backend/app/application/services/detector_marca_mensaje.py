from __future__ import annotations

import re
from difflib import SequenceMatcher


class DetectorMarcaMensaje:
    """SRP: extrae una marca conocida del mensaje del cliente.

    Dos pasos: match exacto contra el vocabulario y, si falla, fuzzy por
    SequenceMatcher sobre tokens de 4+ chars — esto tolera typos como
    'samsun' → 'samsung', 'shony' → 'sony', 'lenobo' → 'lenovo'."""

    _MARCAS: tuple[str, ...] = (
        "acer", "asus", "hp", "lenovo", "dell", "apple", "samsung", "lg",
        "sony", "xiaomi", "huawei", "honor", "infinix", "motorola", "nokia",
        "microsoft", "msi", "gigabyte", "bosch", "philips", "panasonic",
        "whirlpool", "electrolux", "daewoo", "oster", "recco", "haceb",
        "indurama", "mabe", "tcl", "hisense", "jvc", "sankey", "kalley",
        "kernig", "targus", "ugreen", "jbl", "oakley", "brother", "epson",
        "kyocera", "hitech", "mueller", "enxuta", "lemyr", "iffalcon", "flux",
        "tramontina", "toshiba", "nintendo", "playstation", "xbox", "garmin",
        "fitbit", "sat", "zkteco",
    )

    _RX = re.compile(
        r"\b(" + "|".join(_MARCAS) + r"|black\s*\+?\s*decker|klip\s*xtreme|"
        r"master\s*-?\s*g" + r")\b",
        re.IGNORECASE,
    )

    _FUZZY_RATIO_MIN = 0.80

    @classmethod
    def extraer(cls, mensaje: str | None) -> str | None:
        if not mensaje:
            return None
        match = cls._RX.search(mensaje)
        if match:
            return match.group(1).strip().lower()
        return cls._match_fuzzy(mensaje)

    @classmethod
    def _match_fuzzy(cls, mensaje: str) -> str | None:
        mejor: tuple[float, str] | None = None
        for raw in re.findall(r"[a-zA-Z]{4,}", mensaje.lower()):
            for marca in cls._MARCAS:
                if abs(len(raw) - len(marca)) > 2:
                    continue
                ratio = SequenceMatcher(None, raw, marca).ratio()
                if ratio < cls._FUZZY_RATIO_MIN:
                    continue
                if mejor is None or ratio > mejor[0]:
                    mejor = (ratio, marca)
        return mejor[1] if mejor else None
