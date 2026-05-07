from __future__ import annotations

from uuid import UUID

from .....domain.feedback_turnos import FeedbackTurno, VotoFeedback


class FeedbackTurnoMapper:
    """Materializa un FeedbackTurno desde un row crudo."""

    @staticmethod
    def from_row(r: dict) -> FeedbackTurno:
        return FeedbackTurno(
            id=r["id"],
            sesion_id=UUID(r["sesion_id"]),
            turno_index=int(r["turno_index"]),
            mensaje_usuario=r.get("mensaje_usuario"),
            respuesta_agente=r.get("respuesta_agente"),
            voto=VotoFeedback(r["voto"]),
            comentario=r.get("comentario"),
            creado_en=r["creado_en"],
        )
