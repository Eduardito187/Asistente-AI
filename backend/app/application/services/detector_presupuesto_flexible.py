from __future__ import annotations

import re


class DetectorPresupuestoFlexible:

    _PATRON_APROXIMADO = re.compile(
        r"\b(más\s+o\s+menos|mas\s+o\s+menos|aproximadamente|alrededor\s+de|"
        r"unos\s+\d|hasta\s+\d[\d\.]*\s*(bs|bolivianos|bob|usd|\$)?\s*(más\s+o\s+menos|mas\s+o\s+menos))\b",
        re.IGNORECASE,
    )

    _PATRON_PUEDE_ESTIRAR = re.compile(
        r"\b(puedo\s+estirarme|puedo\s+llegar\s+a\s+más|puedo\s+llegar\s+a\s+mas|"
        r"si\s+vale\s+la\s+pena\s+puedo\s+(gastar|pagar)\s+más|"
        r"no\s+es\s+un\s+límite\s+fijo|no\s+es\s+un\s+limite\s+fijo|"
        r"es\s+orientativo|tengo\s+esa\s+idea\s+pero)\b",
        re.IGNORECASE,
    )

    _PATRON_BOLIVIANO_FLEX = re.compile(
        r"\b(tengo\s+como\s+\d|como\s+\d[\d\.]*\s*tengo|más\s+o\s+menos\s+eso\s+tengo|"
        r"mas\s+o\s+menos\s+eso\s+tengo)\b",
        re.IGNORECASE,
    )

    _PATRON_EXACTO = re.compile(
        r"\b(exactamente\s+\d|no\s+más\s+de|no\s+mas\s+de|"
        r"máximo\s+\d[\d\.]*\s*(bs|bolivianos|bob|usd|\$)?\s*y\s+nada\s+más|"
        r"maximo\s+\d[\d\.]*\s*(bs|bolivianos|bob|usd|\$)?\s*y\s+nada\s+mas|"
        r"no\s+tengo\s+más\s+que|no\s+tengo\s+mas\s+que|"
        r"eso\s+es\s+todo\s+lo\s+que\s+tengo|es\s+todo\s+mi\s+presupuesto|"
        r"con\s+eso\s+tengo\s+que\s+arreglarme|"
        r"no\s+puedo\s+pasarme|sin\s+exceder)\b",
        re.IGNORECASE,
    )

    _PATRON_BOLIVIANO_DURO = re.compile(
        r"\b(no\s+llego\s+a\s+más|no\s+llego\s+a\s+mas|"
        r"con\s+\d[\d\.]*\s*(bs|bolivianos|bob|usd|\$)?\s*nomás\s+tengo|"
        r"con\s+\d[\d\.]*\s*(bs|bolivianos|bob|usd|\$)?\s*nomas\s+tengo)\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_flexible(cls, mensaje: str) -> bool:
        return bool(
            cls._PATRON_APROXIMADO.search(mensaje)
            or cls._PATRON_PUEDE_ESTIRAR.search(mensaje)
            or cls._PATRON_BOLIVIANO_FLEX.search(mensaje)
        )

    @classmethod
    def es_duro(cls, mensaje: str) -> bool:
        return bool(
            cls._PATRON_EXACTO.search(mensaje)
            or cls._PATRON_BOLIVIANO_DURO.search(mensaje)
        )
