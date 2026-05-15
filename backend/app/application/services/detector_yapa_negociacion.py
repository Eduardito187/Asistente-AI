from __future__ import annotations

import re


class DetectorYapaNegociacion:

    _PATRON_YAPA = re.compile(
        r"\b(qué\s+me\s+dan\s+de\s+yapa|que\s+me\s+dan\s+de\s+yapa|"
        r"qué\s+viene\s+de\s+yapa|que\s+viene\s+de\s+yapa|"
        r"\bla\s+yapa\b|yapa\s+pe\b|yapa\s+pues\b|de\s+yapa\b|"
        r"qué\s+incluye|que\s+incluye|"
        r"qué\s+me\s+dan\s+con\s+eso|que\s+me\s+dan\s+con\s+eso|"
        r"viene\s+con\s+algo|te\s+dan\s+algo|"
        r"qué\s+viene\s+de\s+bonus|que\s+viene\s+de\s+bonus|"
        r"algo\s+de\s+regalo\s+con\s+la\s+compra|"
        r"dale\s+algo\s+de\s+añadido|dale\s+algo\s+de\s+anadido|"
        r"qué\s+le\s+echan|que\s+le\s+echan|"
        r"qué\s+le\s+meten|que\s+le\s+meten)\b",
        re.IGNORECASE,
    )

    _PATRON_DESCUENTO = re.compile(
        r"\b(me\s+hacen\s+descuento|"
        r"me\s+rebajas?\s+algo|"
        r"me\s+bajas?\s+el\s+precio|"
        r"[¿?]no\s+hay\s+rebaja[?]?|"
        r"[¿?]descuentito[?]?|"
        r"[¿?]no\s+me\s+hacen\s+algo[?]?|"
        r"me\s+hacen\s+precio\b|"
        r"me\s+mejoran\s+el\s+precio|"
        r"me\s+hacen\s+una\s+rebajita|"
        r"me\s+regatean|"
        r"me\s+regalan\s+algo\s+del\s+precio)\b",
        re.IGNORECASE,
    )

    _PATRON_PRECIO_ESPECIAL = re.compile(
        r"\b(al\s+contado\s+cuánto|al\s+contado\s+cuanto|"
        r"si\s+pago\s+al\s+contado|"
        r"en\s+efectivo\s+cuánto|en\s+efectivo\s+cuanto|"
        r"sin\s+tarjeta\s+cuánto|sin\s+tarjeta\s+cuanto|"
        r"pagando\s+cash|"
        r"pago\s+en\s+efectivo\s+cuánto|pago\s+en\s+efectivo\s+cuanto|"
        r"si\s+pago\s+cash)\b",
        re.IGNORECASE,
    )

    @classmethod
    def pide_yapa(cls, mensaje: str) -> bool:
        return bool(cls._PATRON_YAPA.search(mensaje))

    @classmethod
    def pide_descuento(cls, mensaje: str) -> bool:
        return bool(cls._PATRON_DESCUENTO.search(mensaje))

    @classmethod
    def pide_precio_especial(cls, mensaje: str) -> bool:
        return bool(cls._PATRON_PRECIO_ESPECIAL.search(mensaje))
