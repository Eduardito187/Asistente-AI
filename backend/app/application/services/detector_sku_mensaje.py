from __future__ import annotations

import re

# Priorizado: si el mensaje tiene `[XXX-YYY]` (formato tarjeta del agente),
# ese es el SKU canónico. Tildes Ññ permitidas en algunos SKU heredados.
RX_SKU_EN_CORCHETES = re.compile(
    r"\[([A-Z0-9][\w\-.#/()]{2,60})\]",
    re.IGNORECASE,
)
# Fallback: SKU pelado en el texto. Mezcla de letras y dígitos con guión.
RX_SKU_EN_MENSAJE = re.compile(
    r"\b([A-Z0-9]{2,}(?:[-_][A-Z0-9]+)+)\b",
    re.IGNORECASE,
)

# Tokens que parecen SKU pero NO lo son (procesadores, RAM, resoluciones).
# Se filtran del fallback. Si el cliente cita "[I5-13420H]" entre
# corchetes igual gana, pero suelto en el texto se ignora.
_FALSO_POSITIVO_PREFIJO = (
    "I3-", "I5-", "I7-", "I9-",
    "M1", "M2", "M3", "M4",
    "RTX-", "GTX-",
    "DDR4", "DDR5",
    "USB-", "HDMI-",
    "WIFI-",
)


class DetectorSkuMensaje:
    """SRP: extrae un SKU candidato del mensaje del cliente.

    Prioriza SKUs entre corchetes `[XXX-YYY]` (formato tarjeta del agente)
    porque son la cita canónica del catálogo. Fallback: SKU pelado en el
    texto, filtrando tokens que parecen SKU pero son specs (i5-13420H,
    DDR5-4800, etc.)."""

    @classmethod
    def extraer(cls, mensaje: str) -> str | None:
        if not mensaje:
            return None
        # 1. SKU entre corchetes — formato canónico del agente
        match = RX_SKU_EN_CORCHETES.search(mensaje)
        if match:
            candidato = match.group(1).upper()
            if cls._tiene_mezcla_letra_digito(candidato):
                return candidato
        # 2. Fallback: SKU pelado, filtrando specs de hardware
        for match in RX_SKU_EN_MENSAJE.finditer(mensaje):
            candidato = match.group(1).upper()
            if not cls._tiene_mezcla_letra_digito(candidato):
                continue
            if cls._es_falso_positivo(candidato):
                continue
            return candidato
        return None

    @staticmethod
    def _tiene_mezcla_letra_digito(valor: str) -> bool:
        return any(c.isalpha() for c in valor) and any(c.isdigit() for c in valor)

    @staticmethod
    def _es_falso_positivo(valor: str) -> bool:
        return any(valor.startswith(prefijo) for prefijo in _FALSO_POSITIVO_PREFIJO)
