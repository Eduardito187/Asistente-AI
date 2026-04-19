from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from ....domain.feedback_ordenes import FeedbackOrden
from ...ports import UnitOfWork
from .command import RegistrarFeedbackOrdenCommand

log = logging.getLogger("registrar_feedback_orden")


class RegistrarFeedbackOrdenHandler:
    """Handler CQRS: guarda feedback post-orden. Fallar no debe cortar el chat."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarFeedbackOrdenCommand) -> None:
        feedback = FeedbackOrden(
            id=None,
            orden_id=cmd.orden_id,
            sesion_id=cmd.sesion_id,
            rating=cmd.rating,
            comentario=cmd.comentario,
            created_at=datetime.utcnow(),
        )
        try:
            with self._uow_factory() as uow:
                uow.feedback_ordenes.registrar(feedback)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo registrar feedback de orden: %s", exc)
