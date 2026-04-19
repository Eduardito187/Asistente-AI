from __future__ import annotations

import re

from .respuesta_feedback import RespuestaFeedback

RX_RATING_NUM = re.compile(r"\b([1-5])\s*(?:/|de)?\s*(?:5|estrellas?)?\b")
RX_POSITIVO = re.compile(
    r"\b(excelente|genial|perfecto|buenisim[oa]|espectacular|diez|muy bien|"
    r"me encanto|me gusto mucho|increible|super)\b",
    re.IGNORECASE,
)
RX_NEGATIVO = re.compile(
    r"\b(malo|pesimo|horrible|terrible|pesima|mala|lento|demoro|no me gusto|"
    r"confuso|decepcionante|nunca mas)\b",
    re.IGNORECASE,
)
RX_NEUTRO = re.compile(
    r"\b(mas o menos|regular|normal|ok|okay|ni bien ni mal|aceptable|zafa)\b",
    re.IGNORECASE,
)


class DetectorFeedbackRespuesta:
    """SRP: interpretar la respuesta libre del cliente a la pregunta "como
    estuvo la atencion" y derivar un rating (1-5) + comentario."""

    def interpretar(self, mensaje: str) -> RespuestaFeedback | None:
        texto = (mensaje or "").strip()
        if not texto:
            return None
        rating = self._rating_de(texto)
        if rating is None:
            return None
        return RespuestaFeedback(rating=rating, comentario=texto[:500])

    @staticmethod
    def _rating_de(texto: str) -> int | None:
        match = RX_RATING_NUM.search(texto)
        if match:
            valor = int(match.group(1))
            if 1 <= valor <= 5:
                return valor
        if RX_POSITIVO.search(texto):
            return 5
        if RX_NEGATIVO.search(texto):
            return 2
        if RX_NEUTRO.search(texto):
            return 3
        return None
