from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .query import BuscarOrdenSinFeedbackQuery
from .result import ResultadoBuscarOrdenSinFeedback


class BuscarOrdenSinFeedbackHandler:
    """Handler CQRS: encuentra la ultima orden de la sesion sin feedback."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: BuscarOrdenSinFeedbackQuery) -> ResultadoBuscarOrdenSinFeedback:
        with self._uow_factory() as uow:
            orden_id = uow.feedback_ordenes.ultima_orden_sin_feedback(q.sesion_id)
        return ResultadoBuscarOrdenSinFeedback(orden_id=orden_id)
