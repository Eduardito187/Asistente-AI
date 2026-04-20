from __future__ import annotations

import re


class DetectorConsultaDisponibilidad:
    """SRP: detectar preguntas directas de disponibilidad de una categoria,
    tipo 'hay motos?', 'tienen laptops?', 'venden freidoras', 'motos?'.

    Cuando el cliente hace una pregunta corta y directa, y el resolver ya
    matcheo la palabra a una categoria real del catalogo, tiene mas sentido
    responder con una busqueda deterministica que dejar al LLM alucinar."""

    MAX_LEN = 60

    _RX = re.compile(
        r"^\s*(?:"
        r"(?:hay|tien(?:es|en)|vend(?:es|en)|cuentan\s+con|manejan|ofrec(?:es|en)|"
        r"dispon(?:es|en)|consigo|consigue)\s+"
        r"(?:algun(?:a|os|as)?\s+|algun\s+|unos?\s+|unas?\s+|el|la|los|las)?"
        r"[\w\sÁÉÍÓÚÜÑáéíóúüñ]{2,40}\??"
        r"|[\w]{3,40}\??"
        r")\s*$",
        re.IGNORECASE,
    )

    @classmethod
    def es_consulta_disponibilidad(cls, texto: str) -> bool:
        if not texto:
            return False
        texto = texto.strip()
        if len(texto) > cls.MAX_LEN:
            return False
        return bool(cls._RX.match(texto))
