from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.feedback_ordenes import FeedbackOrden, FeedbackOrdenesRepository
from .mappers import FeedbackOrdenMapper
from .sql import FeedbackOrdenSql


class MariaDbFeedbackOrdenesRepository(FeedbackOrdenesRepository):
    """Impl MariaDB del repo de FeedbackOrden."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def registrar(self, feedback: FeedbackOrden) -> int:
        res = self._s.execute(
            text(FeedbackOrdenSql.REGISTRAR),
            {
                "oid": str(feedback.orden_id),
                "sid": str(feedback.sesion_id),
                "rating": feedback.rating,
                "comentario": feedback.comentario,
            },
        )
        return int(res.lastrowid or 0)

    def obtener_por_orden(self, orden_id: UUID) -> Optional[FeedbackOrden]:
        row = (
            self._s.execute(text(FeedbackOrdenSql.POR_ORDEN), {"oid": str(orden_id)})
            .mappings()
            .first()
        )
        return FeedbackOrdenMapper.from_row(dict(row)) if row else None

    def ultima_orden_sin_feedback(self, sesion_id: UUID) -> Optional[UUID]:
        row = (
            self._s.execute(
                text(FeedbackOrdenSql.ULTIMA_ORDEN_SIN_FEEDBACK),
                {"sid": str(sesion_id)},
            )
            .scalar()
        )
        return UUID(row) if row else None

    def listar_recientes(self, limite: int) -> list[FeedbackOrden]:
        rows = (
            self._s.execute(text(FeedbackOrdenSql.LISTAR_RECIENTES), {"lim": int(limite)})
            .mappings()
            .all()
        )
        return [FeedbackOrdenMapper.from_row(dict(r)) for r in rows]
