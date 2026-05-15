from __future__ import annotations

import re


class DetectorYaDecidido:

    _PATRONES = [
        r"me\s+lo\s+recomendaron",
        r"me\s+recomendaron",
        r"me\s+dijeron\s+que",
        r"vi\s+en\s+tiktok",
        r"vi\s+en\s+youtube",
        r"vi\s+en\s+instagram",
        r"lo\s+vi\s+en\s+redes",
        r"sali[oó]\s+en\s+un\s+video",
        r"mi\s+amigo\s+tiene\s+uno",
        r"mi\s+hermano\s+tiene",
        r"mi\s+hermana\s+tiene",
        r"mi\s+mam[aá]\s+tiene",
        r"mi\s+pap[aá]\s+tiene",
        r"mi\s+primo\s+tiene",
        r"mi\s+prima\s+tiene",
        r"mi\s+esposa\s+tiene",
        r"mi\s+esposo\s+tiene",
        r"mi\s+familiar\s+tiene",
        r"ya\s+s[eé]\s+qu[eé]\s+quiero",
        r"ya\s+s[eé]\s+lo\s+que\s+quiero",
        r"ya\s+decid[ií]",
        r"ya\s+me\s+decid[ií]",
        r"quiero\s+exactamente",
        r"quiero\s+espec[ií]ficamente",
        r"me\s+qued[eé]\s+con\s+ganas\s+de",
        r"le\s+puse\s+el\s+ojo\s+a",
        r"ese\s+mismo\s+quiero",
        r"quiero\s+ese\s+mismo",
        r"el\s+mismo\s+que",
        r"igual\s+al\s+que",
        r"tienen\s+el\s+\w",
        r"hay\s+el\s+\w",
        r"est[aá]\s+disponible\s+el",
        r"tienen\s+disponible\s+el",
    ]

    _COMPILED = [re.compile(p, re.IGNORECASE) for p in _PATRONES]

    @classmethod
    def es_ya_decidido(cls, mensaje: str) -> bool:
        for patron in cls._COMPILED:
            if patron.search(mensaje):
                return True
        return False
