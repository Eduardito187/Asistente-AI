from __future__ import annotations

from typing import Callable

from ....domain.carritos import Carrito
from ...ports import UnitOfWork
from .query import VerCarritoQuery


class VerCarritoHandler:
    """Handler CQRS: delega la lectura del carrito al repo."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: VerCarritoQuery) -> Carrito:
        with self._uow_factory() as uow:
            return uow.carritos.obtener(q.sesion_id)
