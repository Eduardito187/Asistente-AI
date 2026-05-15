from __future__ import annotations

import re


class DetectorTamanoFamilia:
    """SRP: extrae el tamaño declarado de la familia del mensaje y lo
    convierte en capacidad mínima de litros para búsquedas de refrigeración.

    Regla empírica estándar para Bolivia/LATAM:
      - 1-2 personas  → 120L mín
      - 3-4 personas  → 200L mín
      - 5-6 personas  → 260L mín
      - 7+  personas  → 320L mín

    Solo activa cuando el mensaje también menciona refrigeración.
    """

    _LITROS_POR_RANGO: list[tuple[int, int, float]] = [
        (1, 2,  120.0),
        (3, 4,  200.0),
        (5, 6,  260.0),
        (7, 99, 320.0),
    ]

    _RX_PERSONAS = re.compile(
        r"\b(?:somos|para|familia\s+de|hogar\s+de|casa\s+de|"
        r"familia\s+numerosa\s+de|grupo\s+de)\s*"
        r"(\d+)\s*(?:personas?|integrantes?|miembros?|personas?\s+en\s+casa)?\b"
        r"|(\d+)\s*(?:personas?|integrantes?|miembros?)\s*(?:en\s+(?:casa|familia|hogar))?",
        re.IGNORECASE,
    )

    _KEYWORDS_REFRIGERACION = re.compile(
        r"\b(?:refri(?:gerador|geradora|geraci[o\xf3]n)?|heladera|refrigerador|"
        r"nevera|frigor[\xed]fico|frigobar)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar_litros_min(cls, mensaje: str) -> float | None:
        """Devuelve la capacidad mínima en litros o None si no hay señal."""
        if not mensaje:
            return None
        if not cls._KEYWORDS_REFRIGERACION.search(mensaje):
            return None
        m = cls._RX_PERSONAS.search(mensaje)
        if not m:
            return None
        raw = m.group(1) or m.group(2)
        if not raw:
            return None
        try:
            n = int(raw)
        except ValueError:
            return None
        for pmin, pmax, litros in cls._LITROS_POR_RANGO:
            if pmin <= n <= pmax:
                return litros
        return None
