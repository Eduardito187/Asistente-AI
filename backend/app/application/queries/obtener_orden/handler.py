from __future__ import annotations

from typing import Callable, Optional

from ....domain.ordenes import Orden
from ...ports import UnitOfWork
from .query import ObtenerOrdenQuery


class ObtenerOrdenHandler:
    """Handler CQRS: busca una orden por numero en el repo."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: ObtenerOrdenQuery) -> Optional[Orden]:
        with self._uow_factory() as uow:
            return uow.ordenes.obtener_por_numero(q.numero_orden)
