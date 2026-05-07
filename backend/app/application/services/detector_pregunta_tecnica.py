from __future__ import annotations

import re


class DetectorPreguntaTecnica:
    """SRP: detecta cuando el mensaje es una pregunta TECNICA legitima
    (specs, compatibilidad, sirve/no sirve, vale la pena, etc).

    Se usa como guard contra falsos handoff: si el cliente esta pidiendo
    honestidad o asesoria tecnica, derivarlo a humano es incorrecto. El
    bot SI puede responder ese tipo de pregunta.

    No invalida senales reales de frustracion (insulto al bot, 'pasame con
    un humano', etc) — solo bloquea cuando la unica senal es algo blando
    como 'no me vendas humo' que se mezcla con una pregunta tecnica."""

    # Pedido de honestidad / anti-humo (no es frustracion, es confianza).
    _RX_PIDE_HONESTIDAD = re.compile(
        r"\bno\s+me\s+vend[ae]s?\s+humo\b"
        r"|\bquiero\s+(?:la\s+)?honestidad\b"
        r"|\bla\s+verdad\s*(?:,|\.|\b)"
        r"|\bs[ée]\s+honest[oa]\b"
        r"|\bsin\s+(?:marketing|cuento|chamuyo)\b"
        r"|\brealmente\s+(?:sirve|vale|conviene|es\s+buena?)\b",
        re.IGNORECASE,
    )

    # Pregunta tecnica: '<algo> sirve/vale/conviene/funciona', '<X> es bueno
    # para <Y>', '<modelo> puede correr <software>', diferencias entre.
    _RX_PREGUNTA_SPECS = re.compile(
        r"\b(?:sirve|vale\s+la\s+pena|conviene|funciona|alcanza|aguanta|"
        r"corre|soporta|rinde|funciona\s+bien|es\s+(?:bueno|buena|suficiente|"
        r"correct[oa]))\b"
        r"|\b(?:diferencia|comparaci[oó]n|comparado)\s+(?:entre|con|de)"
        r"|\bsi\s+(?:una?|el|la)\s+\w+\s+(?:tiene|trae|usa)\s+\w+"
        r"|\b(?:i[357]|ryzen|core|gpu|rtx|gtx|nvidia|amd|intel)\b.*?"
        r"\b(?:sirve|alcanza|funciona|corre|vale)\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_pregunta_tecnica(cls, mensaje: str) -> bool:
        if not mensaje:
            return False
        return bool(
            cls._RX_PIDE_HONESTIDAD.search(mensaje)
            or cls._RX_PREGUNTA_SPECS.search(mensaje)
        )
