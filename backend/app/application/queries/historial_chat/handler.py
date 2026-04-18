from __future__ import annotations

from typing import Callable

from ....domain.chat import Mensaje
from ...ports import UnitOfWork
from .query import HistorialChatQuery


class HistorialChatHandler:
    """Handler CQRS: recupera el historial de la sesion."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: HistorialChatQuery) -> list[Mensaje]:
        with self._uow_factory() as uow:
            return uow.chat.historial(q.sesion_id, limite=q.limite)
