from __future__ import annotations

import re


class DetectorAbandonoTemporal:

    _PATRON = re.compile(
        r"\blo\s+pienso\b"
        r"|voy\s+a\s+pensarlo"
        r"|lo\s+voy\s+a\s+pensar"
        r"|d[eé]jame\s+pensar"
        r"|despu[eé]s\s+vuelvo"
        r"|vuelvo\s+m[aá]s\s+tarde"
        r"|despu[eé]s\s+te\s+consulto"
        r"|luego\s+te\s+escribo"
        r"|d[eé]jame\s+consultar"
        r"|voy\s+a\s+consultar\s+con"
        r"|lo\s+consulto\s+con\s+mi"
        r"|me\s+avisa\s+cuando"
        r"|av[ií]same\s+si\s+baja\s+de\s+precio"
        r"|me\s+avis[aá]s\s+si\s+hay\s+oferta"
        r"|por\s+ahora\s+no\b"
        r"|por\s+ahora\s+estoy\s+viendo"
        r"|solo\s+estoy\s+viendo"
        r"|voy\s+a\s+ver\s+otras\s+opciones"
        r"|voy\s+a\s+comparar\s+en\s+otros\s+lados"
        r"|gracias\s+por\s+ahora"
        r"|ya\s+te\s+escribo"
        r"|voy\s+a\s+ver\s+nom[aá]s"
        r"|lo\s+voy\s+a\s+ver\s+pe\b"
        r"|ya\s+ver[eé]\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_abandono_temporal(cls, mensaje: str) -> bool:
        return bool(cls._PATRON.search(mensaje))
