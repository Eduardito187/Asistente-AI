from __future__ import annotations

import re


class DetectorObjecionDevolucion:

    _PATRON = re.compile(
        r"puedo\s+devolver"
        r"|pol[ií]tica\s+de\s+devoluci[oó]n"
        r"|si\s+no\s+me\s+gusta"
        r"|cambio\s+si\s+no\s+funciona"
        r"|garant[ií]a\s+de\s+devoluci[oó]n"
        r"|devuelven\s+si\s+est[aá]\s+malo"
        r"|plazo\s+de\s+devoluci[oó]n"
        r"|me\s+lo\s+cambian"
        r"|me\s+hacen\s+el\s+cambio"
        r"|qu[eé]\s+pasa\s+si\s+llega\s+malo"
        r"|si\s+viene\s+defectuoso"
        r"|c[oó]mo\s+reclamo"
        r"|quiero\s+un\s+cambio",
        re.IGNORECASE,
    )

    @classmethod
    def es_consulta_devolucion(cls, mensaje: str) -> bool:
        return bool(cls._PATRON.search(mensaje))
