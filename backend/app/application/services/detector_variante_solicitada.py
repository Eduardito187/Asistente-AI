from __future__ import annotations

import re


class DetectorVarianteSolicitada:

    _COLORES = (
        r"negro|blanco|azul|rojo|gris|dorado|plateado|verde"
        r"|morado|rosa|champagne|grafito|midnight"
    )

    _PATRON_VARIANTE = re.compile(
        rf"en\s+({_COLORES})\b"
        rf"|lo\s+tienen\s+en\s+({_COLORES})\b"
        rf"|hay\s+en\s+({_COLORES})\b"
        r"|de\s+\d+\s*gb"
        r"|versi[oó]n\s+de\s+\d+\s*gb"
        r"|el\s+de\s+\d+\s*gb"
        r"|modelo\s+(?:pro|plus|max|ultra|lite|se)\b"
        r"|la\s+versi[oó]n"
        r"|el\s+modelo"
        r"|hay\s+otro\s+color"
        r"|en\s+otro\s+color",
        re.IGNORECASE,
    )

    _PATRON_COLOR = re.compile(
        rf"\b({_COLORES})\b",
        re.IGNORECASE,
    )

    _PATRON_GB = re.compile(
        r"\b(\d+)\s*gb\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_variante(cls, mensaje: str) -> bool:
        return bool(cls._PATRON_VARIANTE.search(mensaje))

    @classmethod
    def color(cls, mensaje: str) -> str | None:
        m = cls._PATRON_COLOR.search(mensaje)
        return m.group(1).lower() if m else None

    @classmethod
    def capacidad_gb(cls, mensaje: str) -> int | None:
        m = cls._PATRON_GB.search(mensaje)
        return int(m.group(1)) if m else None
