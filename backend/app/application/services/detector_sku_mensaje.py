from __future__ import annotations

import re

RX_SKU_EN_MENSAJE = re.compile(
    r"\b([A-Z0-9]{2,}(?:[-_][A-Z0-9]+){1,})\b",
    re.IGNORECASE,
)


class DetectorSkuMensaje:
    """SRP: extrae un SKU candidato del mensaje del cliente.

    Reconoce patrones como `ACE-NHU1PAA001`, `E1504GA-NJ276`, `35101_YALE`
    (al menos un guion o underscore entre bloques alfanumericos). Exige
    mezcla de letras y digitos para evitar capturar palabras como `LAPTOP`.
    """

    @classmethod
    def extraer(cls, mensaje: str) -> str | None:
        if not mensaje:
            return None
        for match in RX_SKU_EN_MENSAJE.finditer(mensaje):
            candidato = match.group(1).upper()
            if cls._tiene_mezcla_letra_digito(candidato):
                return candidato
        return None

    @staticmethod
    def _tiene_mezcla_letra_digito(valor: str) -> bool:
        return any(c.isalpha() for c in valor) and any(c.isdigit() for c in valor)
