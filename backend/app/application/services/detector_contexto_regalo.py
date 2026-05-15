from __future__ import annotations

import re


class DetectorContextoRegalo:
    """Detecta cuando el cliente busca un producto como regalo para otra
    persona. En ese caso el agente debe:
    - Priorizar opciones con buena presentación/packaging
    - Considerar rango de precio moderado (no siempre premium)
    - Preguntar por la persona destinataria si no está claro
    - Sugerir accesorios complementarios como combo regalo"""

    _RX = re.compile(
        r"(?:"
        r"\b(?:de\s+)?regalo\b"
        r"|\bpara\s+regalar\b"
        r"|\bpara\s+(?:el|la|mi|su)\s+cumple(?:a[ñn]os?)?\b"
        r"|\bde\s+cumple(?:a[ñn]os?)?\b"
        r"|\bpor\s+(?:su|el|mi)\s+cumple(?:a[ñn]os?)?\b"
        r"|\bcumple\s+de\b"
        r"|\bdia\s+de\s+(?:la\s+madre|la\s+mujer|la\s+secretaria|"
        r"el\s+padre|los\s+enamorados|san\s+valentin|el\s+nino)"
        r"|\bnavidad\b"
        r"|\ba[ñn]o\s+nuevo\b"
        r"|\bpara\s+(?:mi|su|el|la)\s+(?:wawa|bebe|beb[eé]|nene|nena|"
        r"hijo|hija|nino|nina|nieto|nieta|sobrino|sobrina|primo|prima)"
        r"|\bpara\s+(?:mi|su|el|la)\s+(?:mama|papa|abuela|abuelo|tia|tio|"
        r"hermano|hermana|esposa|esposo|novia|novio|amigo|amiga)"
        r"|\bes\s+(?:un\s+)?obsequio\b"
        r"|\bcomo\s+(?:obsequio|detalle)\b"
        r"|\bsorpresa\b"
        r"|\bpresente\s+(?:de|para)\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_regalo(cls, mensaje: str) -> bool:
        """True cuando el producto buscado es claramente un regalo."""
        if not mensaje:
            return False
        return bool(cls._RX.search(mensaje))

    @classmethod
    def destinatario(cls, mensaje: str) -> str | None:
        """Extrae a quién va el regalo si está mencionado."""
        _RX_DEST = re.compile(
            r"para\s+(?:mi|su|el|la)\s+"
            r"(wawa|bebe|beb[eé]|nene|nena|hijo|hija|nino|nina|nieto|nieta|"
            r"sobrino|sobrina|primo|prima|mama|papa|abuela|abuelo|tia|tio|"
            r"hermano|hermana|esposa|esposo|novia|novio|amigo|amiga)",
            re.IGNORECASE,
        )
        m = _RX_DEST.search(mensaje or "")
        return m.group(1).lower() if m else None
