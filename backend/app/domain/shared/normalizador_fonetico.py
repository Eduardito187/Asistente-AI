from __future__ import annotations

import re


class NormalizadorFonetico:
    """SRP: colapsa equivalencias foneticas del español para matching tolerante
    a typos ortograficos comunes ('cosinas'->'cocinas', 'labadora'->'lavadora',
    'haire'->'aire').

    Aplicada ANTES del ratio de SequenceMatcher, sube el recall de typos que
    cambian una letra por otra del mismo sonido."""

    _RX_CE_CI = re.compile(r"c(?=[ei])")
    _RX_H_INICIAL = re.compile(r"^h")

    @classmethod
    def normalizar(cls, token: str) -> str:
        t = (token or "").lower()
        if not t:
            return t
        # h muda al inicio: 'haire' -> 'aire', 'hola' -> 'ola' (ok, no hay
        # palabras del catalogo que dependan de la h inicial para desambiguar).
        t = cls._RX_H_INICIAL.sub("", t)
        # c suave (ce/ci) -> s: 'cocinas' -> 'cosinas' == 'cosinas' ✓
        t = cls._RX_CE_CI.sub("s", t)
        # b <-> v: colapsar a 'b'. 'labadora' -> 'labadora'; 'lavadora' -> 'labadora'.
        t = t.replace("v", "b")
        # z -> s: 'cozinas' -> 'cosinas'.
        t = t.replace("z", "s")
        # ll -> y: 'calle' -> 'caye'.
        t = t.replace("ll", "y")
        # rr -> r: 'carro' -> 'caro'.
        t = t.replace("rr", "r")
        return t
