from __future__ import annotations

import re


class DetectorCambioCategoria:
    """SRP: detectar si el cliente esta pidiendo cambiar la categoria de busqueda.

    Sin esto, una vez que el perfil bloqueo `categoria_foco='Computadoras'`
    cualquier intento del LLM de buscar en otra categoria queda anulado.
    Pero si el usuario realmente dijo 'ahora quiero una TV', tenemos que
    permitir el cambio. Este detector mira solo el mensaje del turno actual."""

    _RX_CAMBIO = re.compile(
        r"(?:"
        r"\bahora\s+(?:quiero|busco|necesito|me\s+interesa|veamos|veo)\b"
        r"|\bmejor\s+(?:un|una|busco|veamos|cambio|me\s+interesa)\b"
        r"|\bcambio\s+(?:de\s+tema|de\s+producto|de\s+categoria)\b"
        r"|\bya\s+no\s+quiero\b"
        r"|\bolvid(?:a|ate|emos)\s+(?:lo|la|eso|el)\b"
        r"|\botra\s+cosa\b"
        r"|\bnuevo\s+tema\b"
        r"|\bcambiando\s+de\s+tema\b"
        r"|\bdejemos\s+(?:lo|la|eso|el)\b"
        r"|\bmejor\s+busc(?:o|amos|are|aremos)\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def hay_cambio(cls, mensaje: str) -> bool:
        return bool(cls._RX_CAMBIO.search(mensaje or ""))
