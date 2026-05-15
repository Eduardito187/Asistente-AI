from __future__ import annotations

import re


class DetectorConsultaFinanciamiento:
    """Detecta preguntas sobre financiamiento, cuotas, medios de pago.
    Común en Bolivia: QR (Tigo Money, BCP), transferencias, cuotas.
    Cuando dispara, el agente debe mostrar el bloque de financiamiento
    del tool result y mencionar opciones de pago disponibles."""

    _RX = re.compile(
        r"(?:"
        # Cuotas / mensualidades
        r"\ben\s+cuotas?\b"
        r"|\ba\s+cuotas?\b"
        r"|\bcuotas?\s+(?:sin\s+inter[eé]s|mensuales?|semanales?|fijas?)"
        r"|\bpago\s+en\s+cuotas?"
        r"|\bcuantas?\s+cuotas?"
        r"|\bpago\s+mensual\b"
        r"|\bmensualidades?\b"
        # QR / digital (muy usado en Bolivia)
        r"|\bacepta[nt]?\s+(?:qr|pago\s+qr|código\s+qr)"
        r"|\bpago\s+(?:con\s+)?qr\b"
        r"|\bqr\s+(?:de|del?|para)?\s*(?:pago|cobro)?"
        r"|\btigo\s+money\b"
        r"|\bsimple\b"                           # Simple (Banco Unión Bolivia)
        r"|\bbcp\b"                               # BCP Bolivia
        # Tarjeta
        r"|\bcon\s+tarjeta\b"
        r"|\btarjeta\s+de\s+cr[eé]dito\b"
        r"|\btarjeta\s+de\s+d[eé]bito\b"
        r"|\btarjeta\s+(?:visa|mastercard|maestro)\b"
        # Transferencia / depósito
        r"|\btransferencia\b"
        r"|\bdep[oó]sito\s+(?:bancario|en\s+banco)?"
        r"|\bpago\s+online\b"
        # Crédito
        r"|\ba\s+cr[eé]dito\b"
        r"|\ben\s+cr[eé]dito\b"
        r"|\bcr[eé]dito\s+(?:bancario|disponible|aceptan?)?"
        r"|\bfinanciar(?:me|lo|la)?\b"
        r"|\bfinanciamiento\b"
        r"|\bfinanciaci[oó]n\b"
        # Sin interés
        r"|\bsin\s+inter[eé]s\b"
        r"|\b0%\s+inter[eé]s\b"
        # Pago en efectivo (confirmar opción)
        r"|\baceptan?\s+(?:efectivo|cash)\b"
        r"|\bpago\s+(?:en\s+)?efectivo\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_consulta_financiamiento(cls, mensaje: str) -> bool:
        """True cuando el cliente pregunta por formas de pago o financiamiento."""
        if not mensaje:
            return False
        return bool(cls._RX.search(mensaje))
