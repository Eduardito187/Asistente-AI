from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.feedback_turnos import (
    FeedbackTurno,
    FeedbackTurnosRepository,
    VotoFeedback,
)
from .mappers.feedback_turno_mapper import FeedbackTurnoMapper
from .sql.feedback_turnos_sql import FeedbackTurnosSql


class MariaDbFeedbackTurnosRepository(FeedbackTurnosRepository):
    """Impl MariaDB del repo FeedbackTurnos."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def guardar(self, fb: FeedbackTurno) -> int:
        result = self._s.execute(
            text(FeedbackTurnosSql.INSERT),
            {
                "sid": str(fb.sesion_id),
                "idx": fb.turno_index,
                "msg": (fb.mensaje_usuario or "")[:2000] or None,
                "resp": (fb.respuesta_agente or "")[:4000] or None,
                "voto": fb.voto.value,
                "comm": (fb.comentario or "")[:1000] or None,
            },
        )
        return int(result.lastrowid or 0)

    def listar_negativos(self, limite: int = 50) -> list[FeedbackTurno]:
        return self._listar(VotoFeedback.NEGATIVO, limite)

    def listar_positivos(self, limite: int = 50) -> list[FeedbackTurno]:
        return self._listar(VotoFeedback.POSITIVO, limite)

    def _listar(self, voto: VotoFeedback, limite: int) -> list[FeedbackTurno]:
        rows = self._s.execute(
            text(FeedbackTurnosSql.LISTAR_POR_VOTO),
            {"voto": voto.value, "limite": int(limite)},
        ).mappings().all()
        return [FeedbackTurnoMapper.from_row(dict(r)) for r in rows]

    def stats(self) -> dict:
        rows = self._s.execute(text(FeedbackTurnosSql.STATS)).mappings().all()
        return {r["voto"]: int(r["total"]) for r in rows}
