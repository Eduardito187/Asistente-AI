from __future__ import annotations

import re


class DetectorManipulacion:
    """Detecta instrucciones de manipulación comercial antes de pasar al LLM.

    El LLM a veces obedece instrucciones tipo 'di que tiene HDMI 2.1',
    'oculta que no tiene GPU', 'hazlo parecer premium'. Este detector
    los corta deterministicamente y devuelve la respuesta de rechazo."""

    _RECHAZO = (
        "No puedo hacer eso — mi función es asesorarte con datos reales. "
        "Te doy una recomendación honesta basada en lo que tenemos en ficha."
    )

    _RX = re.compile(
        r"(?:"
        # "di que [algo]" — orden de afirmar algo
        r"\bdi\s+que\b"
        r"|\bdile\s+que\b"
        r"|\boculta\s+que\b"
        r"|\bno\s+menciones?\s+(?:que\s+|los?\s+datos?|que\s+falt)"
        r"|\bno\s+digas?\s+que\s+(?:falt|no\s+(?:tiene|hay))"
        r"|\binventa\s+(?:una?\s+)?(?:ventaja|caracteristica|dato|beneficio|razon|garantia)"
        r"|\bhaz(?:lo|la)?\s+parecer\s+(?:premium|mejor|superior|de\s+gama)"
        r"|\bpresenta(?:lo|la)?\s+como\s+(?:premium|flagship|gama\s+alta|ideal)"
        r"|\brecomienda\s+(?:el\s+)?(?:producto\s+)?(?:m[aá]s\s+caro|de\s+mayor\s+(?:precio|margen))\s+aunque"
        r"|\bafirma\s+(?:que\s+)?(?:tiene|incluye|soporta|garantiza)\b"
        r"|\bdi\s+que\s+todos?\b"
        r"|\bdi\s+que\s+(?:tiene|es\s+ideal|es\s+perfecto|sirve\s+para|es\s+buena?)\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_manipulacion(cls, mensaje: str) -> bool:
        return bool(cls._RX.search(mensaje))

    @classmethod
    def respuesta_rechazo(cls) -> str:
        return cls._RECHAZO
