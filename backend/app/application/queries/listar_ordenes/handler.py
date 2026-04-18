from __future__ import annotations

from typing import Callable

from ....domain.ordenes import Orden
from ...ports import UnitOfWork
from .query import ListarOrdenesQuery


class ListarOrdenesHandler:
    """Handler CQRS: delega el listado paginado al repo de ordenes."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: ListarOrdenesQuery) -> list[Orden]:
        with self._uow_factory() as uow:
            return uow.ordenes.listar(limite=max(1, min(q.limite, 500)))
