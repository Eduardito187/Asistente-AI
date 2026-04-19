from __future__ import annotations

from typing import Callable

from ....domain.conversaciones_curadas import ConversacionCurada
from ...ports import UnitOfWork
from .query import ListarConversacionesCuradasQuery


class ListarConversacionesCuradasHandler:
    """Handler CQRS: lista paginada de conversaciones curadas (admin)."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(
        self, q: ListarConversacionesCuradasQuery
    ) -> list[ConversacionCurada]:
        limite = max(1, min(q.limite, 500))
        offset = max(0, q.offset)
        with self._uow_factory() as uow:
            return uow.conversaciones_curadas.listar(limite=limite, offset=offset)
