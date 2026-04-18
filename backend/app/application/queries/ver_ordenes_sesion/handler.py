from __future__ import annotations

from typing import Callable

from ....domain.ordenes import Orden
from ...ports import UnitOfWork
from .query import VerOrdenesSesionQuery


class VerOrdenesSesionHandler:
    """Handler CQRS: devuelve todas las ordenes vinculadas a la sesion."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: VerOrdenesSesionQuery) -> list[Orden]:
        with self._uow_factory() as uow:
            return uow.ordenes.listar_por_sesion(q.sesion_id)
