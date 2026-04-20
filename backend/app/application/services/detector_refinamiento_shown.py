from __future__ import annotations

import re

from .refinamiento_shown import RefinamientoShown


class DetectorRefinamientoShown:
    """Detecta refinamientos contextuales sobre la lista ya mostrada al cliente.

    Ej: tras mostrar 3 motocicletas, el cliente dice 'cuales son electricas?'.
    Ese mensaje no pide un producto nuevo ni es un 'mas barato/otra opcion':
    es un filtro sobre los mostrados. Devolver RefinamientoShown con los
    atributos detectados permite short-circuit deterministico."""

    _RX_GATILLO = re.compile(
        r"\b(?:"
        r"cual(?:es)?\s+(?:son|es|tiene|tienen|de\s+(?:esas|esos|estas|estos))"
        r"|hay\s+(?:alguno|alguna|algun|algunas|algunos)"
        r"|tien(?:es|e|en)\s+(?:alguno|alguna|algun|algunas|algunos)"
        r"|s[oó]lo\s+(?:las|los|el|la|una|uno)"
        r"|de\s+(?:esas|esos|estas|estos|ellas|ellos)\s+cual(?:es)?"
        r"|muestrame\s+(?:las|los|solo|s[oó]lo)"
        r")\b",
        re.IGNORECASE,
    )
    _RX_ELECTRICO_SI = re.compile(
        r"\b(?:el[eé]ctric[oa]s?|a\s+bater[ií]a|sin\s+gasolina)\b",
        re.IGNORECASE,
    )
    _RX_ELECTRICO_NO = re.compile(
        r"\b(?:combusti[oó]n|a\s+gasolina|de\s+gasolina|naftera|nafter[oa]s?)\b",
        re.IGNORECASE,
    )
    _RX_PANEL = re.compile(
        r"\b(OLED|QLED|MINI[\s-]?LED|NANOCELL|LED)\b",
        re.IGNORECASE,
    )
    _RX_RESOLUCION = re.compile(
        r"\b(8K|4K|2K|FHD|HD)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, texto: str) -> RefinamientoShown | None:
        if not texto or not cls._RX_GATILLO.search(texto):
            return None
        refinamiento = RefinamientoShown(
            es_electrico=cls._detectar_es_electrico(texto),
            tipo_panel=cls._detectar_panel(texto),
            resolucion=cls._detectar_resolucion(texto),
        )
        return None if refinamiento.vacio() else refinamiento

    @classmethod
    def _detectar_es_electrico(cls, texto: str) -> bool | None:
        if cls._RX_ELECTRICO_SI.search(texto):
            return True
        if cls._RX_ELECTRICO_NO.search(texto):
            return False
        return None

    @classmethod
    def _detectar_panel(cls, texto: str) -> str | None:
        m = cls._RX_PANEL.search(texto)
        if m is None:
            return None
        return re.sub(r"[\s-]", "", m.group(1)).upper()

    @classmethod
    def _detectar_resolucion(cls, texto: str) -> str | None:
        m = cls._RX_RESOLUCION.search(texto)
        return m.group(1).upper() if m else None
