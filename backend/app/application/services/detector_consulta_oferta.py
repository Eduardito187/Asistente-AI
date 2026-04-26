from __future__ import annotations

import re


class DetectorConsultaOferta:
    """SRP: detecta si el cliente pregunta por descuentos, ofertas o promociones."""

    _RX = re.compile(
        r"\b(ofertas|descuentos|promos|promociones|rebajas|rebajado|rebajados|liquidaci[oó]n)\b"
        r"|(?:qu[eé]|cu[aá]l(?:es)?|hay|tienen|muestrame|ver)\s+(?:est[aá](?:n)?\s+en\s+|en\s+)?"
        r"(?:oferta|descuento|rebaja|promoci[oó]n|precio\s+especial)\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_consulta_oferta(cls, mensaje: str) -> bool:
        return bool(cls._RX.search(mensaje or ""))
