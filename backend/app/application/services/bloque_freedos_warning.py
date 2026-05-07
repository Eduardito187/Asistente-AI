from __future__ import annotations

import re


class BloqueFreedosWarning:
    """SRP: cuando el contexto del turno (mensaje del cliente o categoria
    activa) menciona laptops, inyectar directiva al LLM para que advierta
    explicitamente cuando un producto viene con FreeDOS — el cliente puede
    no saber que NO trae Windows preinstalado y tendra que instalarlo
    aparte para correr software comun (AutoCAD, Office, juegos).

    Nota: el aviso solo aplica si el LLM realmente cita un producto con
    FreeDOS en el SO. Aqui solo damos la directiva; el LLM decide cuando
    aplicarla en base a la ficha real del producto."""

    _RX_LAPTOP = re.compile(
        r"\b(?:laptop|notebook|portatil|portátil|computadora|compu)\b",
        re.IGNORECASE,
    )

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje or not cls._RX_LAPTOP.search(mensaje):
            return None
        return (
            "AVISO FREEDOS: si una laptop citada tiene 'FreeDOS' o 'sin sistema "
            "operativo' en su ficha, agregar EXPLICITAMENTE: 'Viene SIN Windows "
            "preinstalado — hay que instalar Windows aparte (licencia o version "
            "evaluativa) para usar AutoCAD/Office/juegos.' No omitir este aviso."
        )
