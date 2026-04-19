from __future__ import annotations

from uuid import UUID

from ..commands.registrar_feedback_orden import (
    RegistrarFeedbackOrdenCommand,
    RegistrarFeedbackOrdenHandler,
)
from ..queries.buscar_orden_sin_feedback import (
    BuscarOrdenSinFeedbackHandler,
    BuscarOrdenSinFeedbackQuery,
)
from .detector_feedback_respuesta import DetectorFeedbackRespuesta

PREGUNTA_FEEDBACK = (
    "\n\nUna ultima cosita: como te sentiste con la atencion? Podes darme un "
    "puntaje del 1 al 5 o contarme brevemente que tal estuvo — me ayuda a mejorar."
)
CIERRE_AGRADECIMIENTO = "\n\nGracias por la devolucion, la tomamos muy en cuenta!"


class GestorFeedbackPostOrden:
    """SRP: orquestar el ciclo de feedback post-orden dentro del chat.

    - Adjunta la pregunta tras una orden recien confirmada.
    - Intercepta la respuesta del cliente, la interpreta y persiste el rating.
    """

    def __init__(
        self,
        detector: DetectorFeedbackRespuesta,
        registrar: RegistrarFeedbackOrdenHandler,
        buscar_pendiente: BuscarOrdenSinFeedbackHandler,
    ) -> None:
        self._detector = detector
        self._registrar = registrar
        self._buscar_pendiente = buscar_pendiente

    def anexar_pregunta_si_cerro(self, respuesta: str, llevo_a_orden: bool) -> str:
        if not llevo_a_orden:
            return respuesta
        return respuesta + PREGUNTA_FEEDBACK

    def intentar_registrar_respuesta(self, mensaje: str, sesion_id: UUID) -> str | None:
        """Si hay una orden pendiente de feedback y el mensaje trae un rating,
        persiste y devuelve el cierre. Si no aplica, devuelve None."""
        pendiente = self._buscar_pendiente.ejecutar(
            BuscarOrdenSinFeedbackQuery(sesion_id=sesion_id)
        )
        if pendiente.orden_id is None:
            return None
        interpretada = self._detector.interpretar(mensaje)
        if interpretada is None:
            return None
        self._registrar.ejecutar(
            RegistrarFeedbackOrdenCommand(
                orden_id=pendiente.orden_id,
                sesion_id=sesion_id,
                rating=interpretada.rating,
                comentario=interpretada.comentario,
            )
        )
        return CIERRE_AGRADECIMIENTO.strip()
