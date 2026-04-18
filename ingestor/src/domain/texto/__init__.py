from __future__ import annotations

import re
import unicodedata
from typing import Optional


_TAG_RE = re.compile(r"<[^>]+>")
_PRECIO_RE = re.compile(r"[^0-9,\.]")
_WS_RE = re.compile(r"\s+")


class NormalizadorTexto:
    """Operaciones puras de normalización de texto. Sin estado."""

    @staticmethod
    def sin_acentos(s: str) -> str:
        return "".join(
            c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn"
        )

    @staticmethod
    def limpiar_html(v: Optional[str], tope_caracteres: int = 2000) -> Optional[str]:
        if not v:
            return None
        v = _TAG_RE.sub(" ", v)
        v = _WS_RE.sub(" ", v).strip()
        if not v:
            return None
        return v[:tope_caracteres]

    @staticmethod
    def marca_normalizada(v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip()
        if v in {"", "-", "--"}:
            return None
        return v.title() if v.islower() or v.isupper() else v

    @staticmethod
    def precio_bob(v: Optional[str]) -> Optional[float]:
        """Convierte '18.999,00 BOB' o '189,00 BOB' a 18999.00 (formato bo: . miles, , decimal)."""
        if not v:
            return None
        raw = _PRECIO_RE.sub("", v.strip())
        if not raw:
            return None
        raw = raw.replace(".", "").replace(",", ".")
        try:
            return round(float(raw), 2)
        except ValueError:
            return None
