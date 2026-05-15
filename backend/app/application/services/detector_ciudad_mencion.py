from __future__ import annotations
import re


class DetectorCiudadMencion:
    """Detecta la ciudad boliviana que el cliente menciona implícita o explícitamente.
    Permite al agente contextualizar disponibilidad y entrega."""

    _CIUDADES: dict[str, str] = {
        # La Paz y alrededores
        "la paz": "La Paz", "lapaz": "La Paz", "paceño": "La Paz", "paceña": "La Paz",
        "el alto": "El Alto", "viacha": "La Paz",
        # Cochabamba
        "cochabamba": "Cochabamba", "cbba": "Cochabamba", "cocha": "Cochabamba",
        "quillacollo": "Cochabamba", "sacaba": "Cochabamba",
        # Santa Cruz
        "santa cruz": "Santa Cruz", "santa cruz de la sierra": "Santa Cruz",
        "scz": "Santa Cruz", "cruceño": "Santa Cruz", "cruceña": "Santa Cruz",
        "montero": "Santa Cruz", "warnes": "Santa Cruz",
        # Oruro
        "oruro": "Oruro",
        # Potosí
        "potosi": "Potosí", "potosí": "Potosí",
        # Sucre
        "sucre": "Sucre", "chuquisaca": "Sucre",
        # Tarija
        "tarija": "Tarija", "chapacos": "Tarija",
        # Trinidad
        "trinidad": "Trinidad", "beni": "Trinidad",
        # Cobija
        "cobija": "Cobija", "pando": "Cobija",
    }

    _RX = re.compile(
        r"(?:soy\s+de|estoy\s+en|vivo\s+en|desde|para|en)\s+"
        r"(" + "|".join(re.escape(c) for c in sorted(_CIUDADES, key=len, reverse=True)) + r")\b"
        r"|"
        r"\b(" + "|".join(re.escape(c) for c in sorted(_CIUDADES, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, mensaje: str) -> str | None:
        """Retorna la ciudad canónica si se menciona, o None."""
        if not mensaje:
            return None
        m = cls._RX.search(mensaje)
        if not m:
            return None
        raw = (m.group(1) or m.group(2) or "").lower().strip()
        return cls._CIUDADES.get(raw)
