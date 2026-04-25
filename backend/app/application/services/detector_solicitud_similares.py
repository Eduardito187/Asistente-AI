from __future__ import annotations

import re

from .detector_sku_mensaje import DetectorSkuMensaje


class DetectorSolicitudSimilares:
    """SRP: detecta si el cliente pide 'productos similares' a uno especifico.

    Gatillada por el boton 'Similares' de los cards (plantilla fija del
    frontend) y por frases naturales como 'mostrame alternativas',
    'algo parecido', 'otras opciones como este', etc.

    Requiere un SKU en el mensaje — sin referencia especifica no sabemos
    contra que buscar similares."""

    _RX_SIMILARES = re.compile(
        r"\b("
        r"similares?|parecid[oa]s?|alternativas?|"
        r"opciones?\s+como|otros?\s+como|distinto[as]?\s+a|"
        r"diferente[s]?\s+a\s+(?:est[ea]|ese)"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def sku_si_pide_similares(cls, mensaje: str | None) -> str | None:
        """Devuelve el SKU si el mensaje pide similares de un producto
        especifico; None en caso contrario."""
        if not mensaje or not cls._RX_SIMILARES.search(mensaje):
            return None
        return DetectorSkuMensaje.extraer(mensaje)
