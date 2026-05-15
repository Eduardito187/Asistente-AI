from __future__ import annotations

import re


class DetectorObjecionPrecio:

    _PATRONES_OBJECION = [
        r"en\s+otra\s+tienda\s+(est[aá]|sale)\s+m[aá]s\s+barato",
        r"en\s+otro\s+lado\s+(est[aá]|sale)\s+m[aá]s\s+barato",
        r"lo\s+vi\s+m[aá]s\s+barato",
        r"vi\s+m[aá]s\s+barato",
        r"me\s+(lo\s+)?ofrecieron",
        r"me\s+lo\s+dan\s+a",
        r"all[aá]\s+cuesta\s+menos",
        r"all[aá]\s+(est[aá]|sale)\s+m[aá]s\s+barato",
        r"est[aá]\s+muy\s+caro",
        r"es\s+muy\s+caro",
        r"demasiado\s+caro",
        r"sale\s+muy\s+caro",
        r"no\s+vale\s+ese\s+precio",
        r"no\s+vale\s+tanto",
        r"sobrepreciado",
        r"no\s+hay\s+descuento",
        r"no\s+tienen\s+oferta",
        r"no\s+bajan\s+el\s+precio",
        r"ig[uú][aá]lame\s+el\s+precio",
        r"me\s+igualan\s+el\s+precio",
        r"hacen\s+precio",
        r"con\s+factura\s+o\s+sin\s+factura",
        r"sin\s+factura\s+cu[aá]nto",
        r"al\s+contado\s+cu[aá]nto",
        r"al\s+contado\s+cuanto",
        r"sin\s+factura\s+cuanto",
        r"en\s+mercado\s+libre",
        r"en\s+facebook\s+marketplace",
        r"en\s+olx",
        r"est[aá]\s+a\s+\d+",
        r"m[aá]s\s+barato\s+en",
    ]

    _COMPILED_OBJECION = [re.compile(p, re.IGNORECASE) for p in _PATRONES_OBJECION]

    _COMPETIDORES: list[tuple[str, re.Pattern[str]]] = [
        ("fravega", re.compile(r"fravega", re.IGNORECASE)),
        ("casas bahia", re.compile(r"casas\s+bah[ií]a", re.IGNORECASE)),
        ("fnac", re.compile(r"\bfnac\b", re.IGNORECASE)),
        ("mercado libre", re.compile(r"mercado\s+libre", re.IGNORECASE)),
        ("olx", re.compile(r"\bolx\b", re.IGNORECASE)),
        ("facebook", re.compile(r"facebook", re.IGNORECASE)),
        ("falabella", re.compile(r"falabella", re.IGNORECASE)),
        ("hiraoka", re.compile(r"hiraoka", re.IGNORECASE)),
        ("ripley", re.compile(r"ripley", re.IGNORECASE)),
        ("paris", re.compile(r"\bparis\b", re.IGNORECASE)),
        ("linio", re.compile(r"\blinio\b", re.IGNORECASE)),
    ]

    @classmethod
    def es_objecion_precio(cls, mensaje: str) -> bool:
        for patron in cls._COMPILED_OBJECION:
            if patron.search(mensaje):
                return True
        if cls.menciona_competidor(mensaje) is not None:
            return True
        return False

    @classmethod
    def menciona_competidor(cls, mensaje: str) -> str | None:
        for nombre, patron in cls._COMPETIDORES:
            if patron.search(mensaje):
                return nombre
        return None
